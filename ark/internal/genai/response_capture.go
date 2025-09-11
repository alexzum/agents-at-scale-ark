package genai

import (
	"context"
	"sync"

	arkv1alpha1 "mckinsey.com/ark/api/v1alpha1"
)

const ResponseCaptureKey contextKey = "responseCapture"

type ResponseCapture struct {
	mu            sync.Mutex
	teamResponses []arkv1alpha1.TeamResponse
}

func NewResponseCapture() *ResponseCapture {
	return &ResponseCapture{
		teamResponses: make([]arkv1alpha1.TeamResponse, 0),
	}
}

func (rc *ResponseCapture) AddTeamResponse(response arkv1alpha1.TeamResponse) {
	rc.mu.Lock()
	defer rc.mu.Unlock()
	rc.teamResponses = append(rc.teamResponses, response)
}

func (rc *ResponseCapture) GetTeamResponses() []arkv1alpha1.TeamResponse {
	rc.mu.Lock()
	defer rc.mu.Unlock()
	responses := make([]arkv1alpha1.TeamResponse, len(rc.teamResponses))
	copy(responses, rc.teamResponses)
	return responses
}

func ContextWithResponseCapture(ctx context.Context) (context.Context, *ResponseCapture) {
	capture := NewResponseCapture()
	return context.WithValue(ctx, ResponseCaptureKey, capture), capture
}

func ResponseCaptureFromContext(ctx context.Context) *ResponseCapture {
	if capture, ok := ctx.Value(ResponseCaptureKey).(*ResponseCapture); ok {
		return capture
	}
	return nil
}