/* Copyright 2025. McKinsey & Company */

package controller

import (
	"context"
	"crypto/sha256"
	"fmt"
	"slices"
	"strings"
	"time"

	"github.com/go-logr/logr"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/client-go/tools/record"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	logf "sigs.k8s.io/controller-runtime/pkg/log"
	a2aclient "trpc.group/trpc-go/trpc-a2a-go/client"
	"trpc.group/trpc-go/trpc-a2a-go/protocol"

	arkv1alpha1 "mckinsey.com/ark/api/v1alpha1"
	arkv1prealpha1 "mckinsey.com/ark/api/v1prealpha1"
	"mckinsey.com/ark/internal/genai"
)

const (
	statusAssigned  = "assigned"
	statusCompleted = "completed"
	statusFailed    = "failed"
	statusCancelled = "cancelled"
)

type A2ATaskReconciler struct {
	client.Client
	Scheme   *runtime.Scheme
	Recorder record.EventRecorder
}

// +kubebuilder:rbac:groups=ark.mckinsey.com,resources=a2atasks,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=ark.mckinsey.com,resources=a2atasks/finalizers,verbs=update
// +kubebuilder:rbac:groups=ark.mckinsey.com,resources=a2atasks/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=ark.mckinsey.com,resources=queries,verbs=get;list
// +kubebuilder:rbac:groups=ark.mckinsey.com,resources=agents,verbs=get;list

func (r *A2ATaskReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	log := logf.FromContext(ctx)

	var a2aTask arkv1alpha1.A2ATask
	if err := r.Get(ctx, req.NamespacedName, &a2aTask); err != nil {
		log.Error(err, "unable to fetch A2ATask")
		return ctrl.Result{}, client.IgnoreNotFound(err)
	}

	log.Info("Reconciling A2ATask", "taskId", a2aTask.Spec.TaskID, "phase", a2aTask.Status.Phase)

	// Initialize phase if not set
	if a2aTask.Status.Phase == "" {
		a2aTask.Status.Phase = statusPending
	}

	// Handle terminal states
	if isTerminalPhase(a2aTask.Status.Phase) {
		log.Info("A2ATask is in terminal state", "taskId", a2aTask.Spec.TaskID, "phase", a2aTask.Status.Phase)
		return ctrl.Result{}, nil
	}

	// Set start time for new tasks
	if a2aTask.Status.Phase == statusPending && a2aTask.Status.StartTime == nil {
		now := metav1.NewTime(time.Now())
		a2aTask.Status.StartTime = &now
		a2aTask.Status.Phase = statusAssigned

		r.Recorder.Event(&a2aTask, "Normal", "TaskStarted", "A2A task execution started")
	}

	// Poll task status from A2A server if we have the required information
	if a2aTask.Status.Phase == statusAssigned || a2aTask.Status.Phase == statusRunning {
		if err := r.pollA2ATaskStatus(ctx, &a2aTask); err != nil {
			log.Error(err, "failed to poll A2A task status", "taskId", a2aTask.Spec.TaskID)
			r.Recorder.Event(&a2aTask, "Warning", "TaskPollingFailed", fmt.Sprintf("Failed to poll task status: %v", err))

			// Continue with requeue even on error to retry polling
		}
	}

	// Update status
	if err := r.Status().Update(ctx, &a2aTask); err != nil {
		log.Error(err, "unable to update A2ATask status")
		return ctrl.Result{}, err
	}

	// Requeue for non-terminal tasks
	if !isTerminalPhase(a2aTask.Status.Phase) {
		return ctrl.Result{RequeueAfter: time.Second * 3}, nil
	}

	return ctrl.Result{}, nil
}

func (r *A2ATaskReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&arkv1alpha1.A2ATask{}).
		Complete(r)
}

// isTerminalPhase returns true if the task phase represents a terminal state
func isTerminalPhase(phase string) bool {
	terminalPhases := []string{statusCompleted, statusFailed, statusCancelled}
	return slices.Contains(terminalPhases, phase)
}

// pollA2ATaskStatus queries the A2A server for the current task status and updates the A2ATask
func (r *A2ATaskReconciler) pollA2ATaskStatus(ctx context.Context, a2aTask *arkv1alpha1.A2ATask) error {
	a2aClient, err := r.createA2AClient(ctx, a2aTask)
	if err != nil {
		return err
	}

	task, err := r.queryTaskStatus(ctx, a2aClient, a2aTask.Spec.TaskID)
	if err != nil {
		return err
	}

	return r.updateTaskStatus(ctx, a2aTask, task)
}

// createA2AClient creates an A2A client for the task
func (r *A2ATaskReconciler) createA2AClient(ctx context.Context, a2aTask *arkv1alpha1.A2ATask) (*a2aclient.A2AClient, error) {
	// Try annotations first (URLs can't be in labels due to special characters)
	a2aServerAddress, hasAddress := a2aTask.Annotations["ark.mckinsey.com/a2a-server-address"]
	if !hasAddress {
		// Fallback to labels for compatibility
		a2aServerAddress, hasAddress = a2aTask.Labels["ark.mckinsey.com/a2a-server-address"]
		if !hasAddress {
			return nil, fmt.Errorf("A2ATask missing required annotation/label ark.mckinsey.com/a2a-server-address")
		}
	}

	a2aServerName, hasServerName := a2aTask.Annotations["ark.mckinsey.com/a2a-server-name"]
	if !hasServerName {
		// Fallback to labels for compatibility
		a2aServerName, hasServerName = a2aTask.Labels["ark.mckinsey.com/a2a-server-name"]
		if !hasServerName {
			return nil, fmt.Errorf("A2ATask missing required annotation/label ark.mckinsey.com/a2a-server-name")
		}
	}

	var a2aServer arkv1prealpha1.A2AServer
	serverKey := client.ObjectKey{Name: a2aServerName, Namespace: a2aTask.Namespace}
	if err := r.Get(ctx, serverKey, &a2aServer); err != nil {
		return nil, fmt.Errorf("unable to get A2AServer %v: %w", serverKey, err)
	}

	var clientOptions []a2aclient.Option
	if len(a2aServer.Spec.Headers) > 0 {
		resolvedHeaders := make(map[string]string)
		for _, header := range a2aServer.Spec.Headers {
			headerValue, err := genai.ResolveHeaderValueV1PreAlpha1(ctx, r.Client, header, a2aTask.Namespace)
			if err != nil {
				return nil, fmt.Errorf("failed to resolve header %s: %w", header.Name, err)
			}
			resolvedHeaders[header.Name] = headerValue
		}
		// TODO: implement header handling for client
		_ = resolvedHeaders
	}

	return a2aclient.NewA2AClient(a2aServerAddress, clientOptions...)
}

// queryTaskStatus queries the A2A server for task status
func (r *A2ATaskReconciler) queryTaskStatus(ctx context.Context, a2aClient *a2aclient.A2AClient, taskID string) (*protocol.Task, error) {
	historyLength := 100
	params := protocol.TaskQueryParams{
		ID:            taskID,
		HistoryLength: &historyLength,
	}
	task, err := a2aClient.GetTasks(ctx, params)
	if err != nil {
		return nil, fmt.Errorf("failed to get task status from A2A server: %w", err)
	}
	return task, nil
}

func (r *A2ATaskReconciler) mergeArtifacts(existingTask, newTaskData *arkv1alpha1.A2ATaskTask, taskID string, log logr.Logger) {
	existingArtifactIds := make(map[string]bool)
	for _, artifact := range existingTask.Artifacts {
		existingArtifactIds[artifact.ArtifactID] = true
	}

	for _, newArtifact := range newTaskData.Artifacts {
		if !existingArtifactIds[newArtifact.ArtifactID] {
			existingTask.Artifacts = append(existingTask.Artifacts, newArtifact)
			log.Info("added new artifact", "taskId", taskID, "artifactId", newArtifact.ArtifactID)
		}
	}
}

func (r *A2ATaskReconciler) mergeHistory(existingTask, newTaskData *arkv1alpha1.A2ATaskTask, taskID string, log logr.Logger) {
	if len(newTaskData.History) == 0 {
		return
	}

	existingMessages := make(map[string]bool)
	for _, existingMsg := range existingTask.History {
		msgKey := r.generateMessageKey(existingMsg)
		existingMessages[msgKey] = true
	}

	for _, newMsg := range newTaskData.History {
		msgKey := r.generateMessageKey(newMsg)
		if !existingMessages[msgKey] {
			existingTask.History = append(existingTask.History, newMsg)
			existingMessages[msgKey] = true
			log.Info("added new history message", "taskId", taskID, "messageKey", msgKey[:8], "totalHistory", len(existingTask.History))
		}
	}
}

func (r *A2ATaskReconciler) updateTaskPhase(a2aTask *arkv1alpha1.A2ATask, task *protocol.Task, log logr.Logger) {
	newPhase := convertA2AStateToPhase(string(task.Status.State))
	if newPhase != a2aTask.Status.Phase {
		log.Info("task phase changed", "taskId", task.ID, "oldPhase", a2aTask.Status.Phase, "newPhase", newPhase)
		a2aTask.Status.Phase = newPhase

		if isTerminalPhase(newPhase) {
			now := metav1.NewTime(time.Now())
			a2aTask.Status.CompletionTime = &now
			r.Recorder.Event(a2aTask, "Normal", "TaskCompleted",
				fmt.Sprintf("A2A task completed with status: %s", newPhase))
		}
	}
}

func (r *A2ATaskReconciler) updateTaskProgress(a2aTask *arkv1alpha1.A2ATask, task *protocol.Task, log logr.Logger) {
	progressValue, hasProgress := task.Metadata["progress"]
	if !hasProgress {
		return
	}

	progressStr, ok := progressValue.(string)
	if !ok {
		return
	}

	var progress int32
	if _, parseErr := fmt.Sscanf(progressStr, "%d", &progress); parseErr == nil {
		a2aTask.Status.Progress = progress
		log.Info("updated task progress", "taskId", task.ID, "progress", progress)
	}
}

// updateTaskStatus updates the A2ATask status with information from the A2A server
func (r *A2ATaskReconciler) updateTaskStatus(ctx context.Context, a2aTask *arkv1alpha1.A2ATask, task *protocol.Task) error {
	if task == nil {
		return nil
	}

	log := logf.FromContext(ctx)
	log.Info("received updated task status", "taskId", task.ID, "state", task.Status.State)

	newTaskData := arkv1alpha1.ConvertTaskFromProtocol(task)

	if a2aTask.Status.Task == nil {
		a2aTask.Status.Task = &newTaskData
		r.updateTaskPhase(a2aTask, task, log)
		r.updateTaskProgress(a2aTask, task, log)
		return nil
	}

	existingTask := a2aTask.Status.Task
	r.mergeArtifacts(existingTask, &newTaskData, task.ID, log)
	r.mergeHistory(existingTask, &newTaskData, task.ID, log)

	existingTask.Status = newTaskData.Status
	existingTask.Metadata = newTaskData.Metadata
	existingTask.SessionID = newTaskData.SessionID

	r.updateTaskPhase(a2aTask, task, log)
	r.updateTaskProgress(a2aTask, task, log)

	return nil
}

// convertA2AStateToPhase converts A2A protocol task states to K8s A2ATask phases
func convertA2AStateToPhase(state string) string {
	switch state {
	case "submitted":
		return statusAssigned
	case "working":
		return statusRunning
	case "completed":
		return statusCompleted
	case "failed":
		return statusFailed
	case "canceled", "cancelled":
		return statusCancelled
	case "rejected":
		return statusFailed
	case "input-required", "auth-required":
		return statusRunning // Keep running until resolved
	default:
		return statusRunning
	}
}

// generateMessageKey creates a unique key for a message based on its content
// This key is used to determine if a message already exists in the history
func (r *A2ATaskReconciler) generateMessageKey(msg arkv1alpha1.A2ATaskMessage) string {
	var content strings.Builder

	// Include role
	content.WriteString(msg.Role)
	content.WriteString("|")

	// Include all text parts content
	for i, part := range msg.Parts {
		if i > 0 {
			content.WriteString("||")
		}
		content.WriteString(part.Kind)
		content.WriteString(":")
		switch part.Kind {
		case "text":
			content.WriteString(part.Text)
		case "data":
			content.WriteString(part.Data)
		case "file":
			content.WriteString(part.URI)
			content.WriteString(part.MimeType)
		}
	}

	// Create a hash of the content to keep the key manageable
	hash := sha256.Sum256([]byte(content.String()))
	return fmt.Sprintf("%x", hash)
}

// Force devspace reload ven  5 set 2025 14:30:15 CEST - Added HistoryLength to TaskQueryParams
