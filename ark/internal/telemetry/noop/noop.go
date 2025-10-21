/* Copyright 2025. McKinsey & Company */

package noop

import (
	"context"

	"mckinsey.com/ark/internal/telemetry"
)

// noopTracer is a zero-overhead tracer that does nothing.
type noopTracer struct{}

// NewTracer creates a no-op tracer.
func NewTracer() telemetry.Tracer {
	return &noopTracer{}
}

func (t *noopTracer) Start(ctx context.Context, spanName string, opts ...telemetry.SpanOption) (context.Context, telemetry.Span) {
	return ctx, &noopSpan{}
}

// noopSpan is a zero-overhead span that does nothing.
// All methods are intentionally empty for zero-overhead no-op behavior.
type noopSpan struct{}

func (s *noopSpan) End()                                                    {} //nolint:revive
func (s *noopSpan) SetAttributes(attributes ...telemetry.Attribute)         {} //nolint:revive
func (s *noopSpan) RecordError(err error)                                   {} //nolint:revive
func (s *noopSpan) SetStatus(status telemetry.Status, description string)   {} //nolint:revive
func (s *noopSpan) AddEvent(name string, attributes ...telemetry.Attribute) {} //nolint:revive

// noopQueryRecorder is a zero-overhead query recorder that does nothing.
// All methods are intentionally empty for zero-overhead no-op behavior.
type noopQueryRecorder struct{}

// NewQueryRecorder creates a no-op query recorder.
func NewQueryRecorder() telemetry.QueryRecorder {
	return &noopQueryRecorder{}
}

func (r *noopQueryRecorder) StartQuery(ctx context.Context, queryName, queryNamespace, phase string) (context.Context, telemetry.Span) {
	return ctx, &noopSpan{}
}

func (r *noopQueryRecorder) StartTarget(ctx context.Context, targetType, targetName string) (context.Context, telemetry.Span) {
	return ctx, &noopSpan{}
}

func (r *noopQueryRecorder) RecordInput(span telemetry.Span, content string)       {} //nolint:revive
func (r *noopQueryRecorder) RecordOutput(span telemetry.Span, content string)      {} //nolint:revive
func (r *noopQueryRecorder) RecordMessages(span telemetry.Span, messages []string) {} //nolint:revive
func (r *noopQueryRecorder) RecordTokenUsage(span telemetry.Span, promptTokens, completionTokens, totalTokens int64) {
} //nolint:revive
func (r *noopQueryRecorder) RecordModelDetails(span telemetry.Span, modelName, provider, modelType string) {
}                                                                                  //nolint:revive
func (r *noopQueryRecorder) RecordSessionID(span telemetry.Span, sessionID string) {} //nolint:revive
func (r *noopQueryRecorder) RecordSuccess(span telemetry.Span)                     {} //nolint:revive
func (r *noopQueryRecorder) RecordError(span telemetry.Span, err error)            {} //nolint:revive
