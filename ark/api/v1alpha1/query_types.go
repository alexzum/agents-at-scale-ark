/* Copyright 2025. McKinsey & Company */

package v1alpha1

import (
	"encoding/json"
	"fmt"

	"github.com/openai/openai-go"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
)

const (
	// QueryTypeUser represents a query with string input that gets converted to a single message with role="user"
	QueryTypeUser = "user"
	// QueryTypeMessages represents a query with an array of OpenAI ChatCompletionMessageParamUnion objects
	QueryTypeMessages = "messages"
)

type QueryTarget struct {
	// +kubebuilder:validation:Required
	// +kubebuilder:validation:Enum=agent;team;model;tool
	Type string `json:"type"`
	// +kubebuilder:validation:Required
	// +kubebuilder:validation:MinLength=1
	Name string `json:"name"`
}

type MemoryRef struct {
	// +kubebuilder:validation:Required
	// +kubebuilder:validation:MinLength=1
	Name string `json:"name"`
	// +kubebuilder:validation:Optional
	Namespace string `json:"namespace,omitempty"`
}

type QuerySpec struct {
	// +kubebuilder:validation:Optional
	// +kubebuilder:validation:Enum=user;messages
	// +kubebuilder:default=user
	Type string `json:"type,omitempty"`
	// +kubebuilder:validation:Required
	// +kubebuilder:pruning:PreserveUnknownFields
	// +kubebuilder:validation:Schemaless
	// Input can be a string (type=user) or []openai.ChatCompletionMessageParamUnion (type=messages)
	Input runtime.RawExtension `json:"input"`
	// +kubebuilder:validation:Optional
	// Parameters for template processing in the input field
	Parameters []Parameter `json:"parameters,omitempty"`
	// +kubebuilder:validation:Optional
	Targets []QueryTarget `json:"targets,omitempty"`
	// +kubebuilder:validation:Optional
	Selector *metav1.LabelSelector `json:"selector,omitempty"`
	// +kubebuilder:validation:Optional
	Memory *MemoryRef `json:"memory,omitempty"`
	// +kubebuilder:validation:Optional
	// +kubebuilder:validation:MinLength=1
	ServiceAccount string `json:"serviceAccount,omitempty"`
	// +kubebuilder:validation:Optional
	// +kubebuilder:validation:MinLength=1
	SessionId string `json:"sessionId,omitempty"`
	// +kubebuilder:validation:Optional
	// +kubebuilder:default="720h"
	TTL *metav1.Duration `json:"ttl,omitempty"`
	// +kubebuilder:default="5m"
	// Timeout for query execution (e.g., "30s", "5m", "1h")
	Timeout *metav1.Duration `json:"timeout,omitempty"`
	// +kubebuilder:validation:Optional
	// When true, indicates intent to cancel the query
	Cancel bool `json:"cancel,omitempty"`
}

// Response defines a response from a query target.
type Response struct {
	Target  QueryTarget `json:"target,omitempty"`
	Content string      `json:"content,omitempty"`
	Raw     string      `json:"raw,omitempty"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:printcolumn:name="Type",type=string,JSONPath=`.spec.type`
// +kubebuilder:printcolumn:name="Phase",type=string,JSONPath=`.status.phase`
// +kubebuilder:printcolumn:name="Duration",type=string,JSONPath=`.status.duration`
// +kubebuilder:printcolumn:name="Age",type=date,JSONPath=`.metadata.creationTimestamp`

type Query struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   QuerySpec   `json:"spec,omitempty"`
	Status QueryStatus `json:"status,omitempty"`
}

type TokenUsage struct {
	PromptTokens     int64 `json:"promptTokens,omitempty"`
	CompletionTokens int64 `json:"completionTokens,omitempty"`
	TotalTokens      int64 `json:"totalTokens,omitempty"`
}

type QueryStatus struct {
	// +kubebuilder:default="pending"
	// +kubebuilder:validation:Enum=pending;running;error;done;canceled
	Phase      string     `json:"phase,omitempty"`
	Responses  []Response `json:"responses,omitempty"`
	TokenUsage TokenUsage `json:"tokenUsage,omitempty"`
	// +kubebuilder:validation:Optional
	Duration *metav1.Duration `json:"duration,omitempty"`
}

// +kubebuilder:object:root=true
type QueryList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []Query `json:"items"`
}

// GetInputString returns the input as a string when type="user" or type is empty (default)
func (q *QuerySpec) GetInputString() (string, error) {
	if q.Type != "" && q.Type != QueryTypeUser {
		return "", fmt.Errorf("cannot get string input for type=%s, expected type=%s or empty", q.Type, QueryTypeUser)
	}

	var inputString string
	if err := json.Unmarshal(q.Input.Raw, &inputString); err != nil {
		return "", fmt.Errorf("failed to unmarshal input as string: %w", err)
	}

	return inputString, nil
}

// GetInputMessages returns the input as []openai.ChatCompletionMessageParamUnion when type="messages"
func (q *QuerySpec) GetInputMessages() ([]openai.ChatCompletionMessageParamUnion, error) {
	if q.Type != QueryTypeMessages {
		return nil, fmt.Errorf("cannot get message input for type=%s, expected type=%s", q.Type, QueryTypeMessages)
	}

	var messages []openai.ChatCompletionMessageParamUnion

	// First try to unmarshal directly as array (for backward compatibility)
	if err := json.Unmarshal(q.Input.Raw, &messages); err == nil {
		return messages, nil
	}

	// If that fails, try to unmarshal as a JSON string first, then as array
	var inputString string
	if err := json.Unmarshal(q.Input.Raw, &inputString); err != nil {
		return nil, fmt.Errorf("failed to unmarshal input as string: %w", err)
	}

	if err := json.Unmarshal([]byte(inputString), &messages); err != nil {
		return nil, fmt.Errorf("failed to unmarshal input as messages: %w", err)
	}

	return messages, nil
}

// SetInputString sets the input as a string and updates type to "user" (or keeps it empty for default)
func (q *QuerySpec) SetInputString(input string) error {
	inputBytes, err := json.Marshal(input)
	if err != nil {
		return fmt.Errorf("failed to marshal string input: %w", err)
	}

	// Set type to QueryTypeUser if not already set, or keep empty for default behavior
	if q.Type == "" {
		q.Type = QueryTypeUser // Make it explicit
	}
	q.Input.Raw = inputBytes
	return nil
}

// SetInputMessages sets the input as []openai.ChatCompletionMessageParamUnion and updates type to "messages"
func (q *QuerySpec) SetInputMessages(messages []openai.ChatCompletionMessageParamUnion) error {
	inputBytes, err := json.Marshal(messages)
	if err != nil {
		return fmt.Errorf("failed to marshal message input: %w", err)
	}

	q.Type = QueryTypeMessages
	q.Input.Raw = inputBytes
	return nil
}

// GetInputAsGeneric returns the input as either string or []openai.ChatCompletionMessageParamUnion based on type
func (q *QuerySpec) GetInputAsGeneric() (interface{}, error) {
	switch q.Type {
	case QueryTypeUser, "": // Empty type defaults to user/string input
		return q.GetInputString()
	case QueryTypeMessages:
		return q.GetInputMessages()
	default:
		return nil, fmt.Errorf("unknown input type: %s", q.Type)
	}
}

func init() {
	SchemeBuilder.Register(&Query{}, &QueryList{})
}
