/* Copyright 2025. McKinsey & Company */

package v1alpha1

import (
	"fmt"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"trpc.group/trpc-go/trpc-a2a-go/protocol"
)

type AgentRef struct {
	// +kubebuilder:validation:Optional
	Name string `json:"name,omitempty"`
	// +kubebuilder:validation:Optional
	Namespace string `json:"namespace,omitempty"`
}

// A2ATaskPart represents content parts compatible with A2A protocol
type A2ATaskPart struct {
	// +kubebuilder:validation:Required
	// +kubebuilder:validation:Enum=text;file;data
	Kind string `json:"kind"`
	// +kubebuilder:validation:Optional
	Text string `json:"text,omitempty"`
	// +kubebuilder:validation:Optional
	Data string `json:"data,omitempty"`
	// +kubebuilder:validation:Optional
	MimeType string `json:"mimeType,omitempty"`
	// +kubebuilder:validation:Optional
	URI string `json:"uri,omitempty"`
	// +kubebuilder:validation:Optional
	Metadata map[string]string `json:"metadata,omitempty"`
}

// A2ATaskArtifact represents artifacts from A2A protocol
type A2ATaskArtifact struct {
	// +kubebuilder:validation:Required
	// +kubebuilder:validation:MinLength=1
	ArtifactID string `json:"artifactId"`
	// +kubebuilder:validation:Optional
	Name string `json:"name,omitempty"`
	// +kubebuilder:validation:Optional
	Description string `json:"description,omitempty"`
	// +kubebuilder:validation:Required
	Parts []A2ATaskPart `json:"parts"`
	// +kubebuilder:validation:Optional
	Metadata map[string]string `json:"metadata,omitempty"`
}

// A2ATaskMessage represents messages from A2A protocol
type A2ATaskMessage struct {
	// +kubebuilder:validation:Required
	// +kubebuilder:validation:Enum=user;agent;system
	Role string `json:"role"`
	// +kubebuilder:validation:Required
	Parts []A2ATaskPart `json:"parts"`
	// +kubebuilder:validation:Optional
	Metadata map[string]string `json:"metadata,omitempty"`
}

// A2ATaskStatus represents task status from A2A protocol
type A2ATaskTaskStatus struct {
	// +kubebuilder:validation:Required
	// +kubebuilder:validation:Enum=submitted;working;input-required;completed;canceled;failed;rejected;auth-required;unknown
	State string `json:"state"`
	// +kubebuilder:validation:Optional
	Message *A2ATaskMessage `json:"message,omitempty"`
	// +kubebuilder:validation:Optional
	Timestamp string `json:"timestamp,omitempty"`
}

// A2ATaskTask represents the full A2A task structure
type A2ATaskTask struct {
	// +kubebuilder:validation:Required
	// +kubebuilder:validation:MinLength=1
	ID string `json:"id"`
	// +kubebuilder:validation:Optional
	SessionID string `json:"sessionId,omitempty"`
	// +kubebuilder:validation:Required
	Status A2ATaskTaskStatus `json:"status"`
	// +kubebuilder:validation:Optional
	Artifacts []A2ATaskArtifact `json:"artifacts,omitempty"`
	// +kubebuilder:validation:Optional
	History []A2ATaskMessage `json:"history,omitempty"`
	// +kubebuilder:validation:Optional
	Metadata map[string]string `json:"metadata,omitempty"`
}

type A2ATaskSpec struct {
	// +kubebuilder:validation:Required
	QueryRef QueryRef `json:"queryRef"`
	// +kubebuilder:validation:Required
	// +kubebuilder:validation:MinLength=1
	TaskID string `json:"taskId"`
	// +kubebuilder:validation:Optional
	ContextID string `json:"contextId,omitempty"`
	// +kubebuilder:validation:Optional
	Input string `json:"input,omitempty"`
	// +kubebuilder:validation:Optional
	Parameters map[string]string `json:"parameters,omitempty"`
	// +kubebuilder:validation:Optional
	// +kubebuilder:default=0
	Priority int32 `json:"priority,omitempty"`
	// +kubebuilder:validation:Optional
	// +kubebuilder:default="5m"
	Timeout *metav1.Duration `json:"timeout,omitempty"`
}

type A2ATaskStatus struct {
	// +kubebuilder:validation:Optional
	// +kubebuilder:default="pending"
	// +kubebuilder:validation:Enum=pending;assigned;running;completed;failed;cancelled
	Phase string `json:"phase,omitempty"`
	// +kubebuilder:validation:Optional
	AssignedAgent *AgentRef `json:"assignedAgent,omitempty"`
	// +kubebuilder:validation:Optional
	StartTime *metav1.Time `json:"startTime,omitempty"`
	// +kubebuilder:validation:Optional
	CompletionTime *metav1.Time `json:"completionTime,omitempty"`
	// +kubebuilder:validation:Optional
	Error string `json:"error,omitempty"`
	// +kubebuilder:validation:Optional
	// Use A2A protocol types directly
	Task *A2ATaskTask `json:"task,omitempty"`
	// +kubebuilder:validation:Optional
	// +kubebuilder:validation:Minimum=0
	// +kubebuilder:validation:Maximum=100
	Progress int32 `json:"progress,omitempty"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:printcolumn:name="Phase",type=string,JSONPath=`.status.phase`
// +kubebuilder:printcolumn:name="Task ID",type=string,JSONPath=`.spec.taskId`
// +kubebuilder:printcolumn:name="Context ID",type=string,JSONPath=`.spec.contextId`
// +kubebuilder:printcolumn:name="Query",type=string,JSONPath=`.spec.queryRef.name`
// +kubebuilder:printcolumn:name="Assigned Agent",type=string,JSONPath=`.status.assignedAgent.name`
// +kubebuilder:printcolumn:name="Age",type=date,JSONPath=`.metadata.creationTimestamp`

type A2ATask struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   A2ATaskSpec   `json:"spec,omitempty"`
	Status A2ATaskStatus `json:"status,omitempty"`
}

// +kubebuilder:object:root=true
type A2ATaskList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []A2ATask `json:"items"`
}

func init() {
	SchemeBuilder.Register(&A2ATask{}, &A2ATaskList{})
}

// Conversion functions between A2A protocol types and K8s-compatible types

// ConvertPartFromProtocol converts a protocol.Part to A2ATaskPart
func ConvertPartFromProtocol(part interface{}) A2ATaskPart {
	switch p := part.(type) {
	case *protocol.TextPart:
		return A2ATaskPart{
			Kind: "text",
			Text: p.Text,
		}
	case *protocol.DataPart:
		return A2ATaskPart{
			Kind: "data",
			Data: fmt.Sprintf("%v", p.Data),
		}
	case *protocol.FilePart:
		taskPart := A2ATaskPart{
			Kind: "file",
		}
		if fileWithURI, ok := p.File.(*protocol.FileWithURI); ok {
			taskPart.URI = fileWithURI.URI
			if fileWithURI.MimeType != nil {
				taskPart.MimeType = *fileWithURI.MimeType
			}
		}
		if fileWithBytes, ok := p.File.(*protocol.FileWithBytes); ok {
			taskPart.Data = fileWithBytes.Bytes // base64 content
			if fileWithBytes.MimeType != nil {
				taskPart.MimeType = *fileWithBytes.MimeType
			}
		}
		return taskPart
	default:
		return A2ATaskPart{
			Kind: "text",
			Text: "unknown part type",
		}
	}
}

// ConvertPartToProtocol converts A2ATaskPart to protocol.Part
func ConvertPartToProtocol(part A2ATaskPart) protocol.Part {
	switch part.Kind {
	case "text":
		return protocol.NewTextPart(part.Text)
	case "data":
		return protocol.NewDataPart(part.Data)
	case "file":
		if part.URI != "" {
			return protocol.NewFilePartWithURI("", part.MimeType, part.URI)
		}
		return protocol.NewTextPart("file part without URI")
	default:
		return protocol.NewTextPart(part.Text)
	}
}

func convertArtifactsFromProtocol(protocolArtifacts []protocol.Artifact) []A2ATaskArtifact {
	artifacts := make([]A2ATaskArtifact, 0, len(protocolArtifacts))
	for _, artifact := range protocolArtifacts {
		var parts []A2ATaskPart
		for _, part := range artifact.Parts {
			parts = append(parts, ConvertPartFromProtocol(part))
		}

		metadata := convertMetadataToStringMap(artifact.Metadata)

		if len(parts) > 0 {
			taskArtifact := A2ATaskArtifact{
				ArtifactID: artifact.ArtifactID,
				Parts:      parts,
				Metadata:   metadata,
			}
			if artifact.Name != nil {
				taskArtifact.Name = *artifact.Name
			}
			if artifact.Description != nil {
				taskArtifact.Description = *artifact.Description
			}
			artifacts = append(artifacts, taskArtifact)
		}
	}
	return artifacts
}

func convertHistoryFromProtocol(protocolHistory []protocol.Message) []A2ATaskMessage {
	history := make([]A2ATaskMessage, 0, len(protocolHistory))
	for _, msg := range protocolHistory {
		var msgParts []A2ATaskPart
		for _, part := range msg.Parts {
			msgParts = append(msgParts, ConvertPartFromProtocol(part))
		}

		msgMetadata := convertMetadataToStringMap(msg.Metadata)

		if len(msgParts) > 0 {
			historyMessage := A2ATaskMessage{
				Role:     string(msg.Role),
				Parts:    msgParts,
				Metadata: msgMetadata,
			}
			history = append(history, historyMessage)
		}
	}
	return history
}

func convertStatusMessageFromProtocol(statusMessage *protocol.Message) (*A2ATaskMessage, []A2ATaskPart) {
	if statusMessage == nil {
		return nil, nil
	}

	msgParts := make([]A2ATaskPart, 0, len(statusMessage.Parts))
	for _, part := range statusMessage.Parts {
		msgParts = append(msgParts, ConvertPartFromProtocol(part))
	}

	msgMetadata := convertMetadataToStringMap(statusMessage.Metadata)

	message := &A2ATaskMessage{
		Role:     string(statusMessage.Role),
		Parts:    msgParts,
		Metadata: msgMetadata,
	}

	return message, msgParts
}

func convertMetadataToStringMap(metadata map[string]any) map[string]string {
	result := make(map[string]string)
	for k, v := range metadata {
		result[k] = fmt.Sprintf("%v", v)
	}
	return result
}

// ConvertTaskFromProtocol converts a protocol.Task to A2ATaskTask
func ConvertTaskFromProtocol(task *protocol.Task) A2ATaskTask {
	artifacts := convertArtifactsFromProtocol(task.Artifacts)
	history := convertHistoryFromProtocol(task.History)
	taskMetadata := convertMetadataToStringMap(task.Metadata)

	message, msgParts := convertStatusMessageFromProtocol(task.Status.Message)
	if len(msgParts) > 0 {
		history = append(history, *message)
	}

	return A2ATaskTask{
		ID:        task.ID,
		SessionID: task.ContextID,
		Status: A2ATaskTaskStatus{
			State:     string(task.Status.State),
			Message:   message,
			Timestamp: task.Status.Timestamp,
		},
		Artifacts: artifacts,
		History:   history,
		Metadata:  taskMetadata,
	}
}
