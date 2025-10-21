/* Copyright 2025. McKinsey & Company */

package telemetry

import (
	"context"
	"time"
)

// Tracer creates and manages spans for distributed tracing.
// Decouples ARK controllers from specific tracing implementations (OTEL, Jaeger, etc.).
type Tracer interface {
	// Start begins a new span. Returns a new context containing the span.
	// The span must be ended by calling End().
	Start(ctx context.Context, spanName string, opts ...SpanOption) (context.Context, Span)
}

// Span represents a single operation within a trace.
// Safe for concurrent attribute/event recording. Immutable once ended.
type Span interface {
	End()
	SetAttributes(attributes ...Attribute)
	RecordError(err error)
	SetStatus(status Status, description string)
	AddEvent(name string, attributes ...Attribute)
}

// SpanOption configures span creation behavior.
type SpanOption interface {
	applySpanOption(*spanConfig)
}

// spanConfig holds span creation configuration.
type spanConfig struct {
	attributes []Attribute
	spanKind   SpanKind
	timestamp  time.Time
}

// Attribute represents a key-value pair attached to spans or events.
type Attribute struct {
	Key   string
	Value interface{}
}

// SpanKind follows OpenTelemetry span kind semantics.
type SpanKind int

const (
	SpanKindInternal SpanKind = iota
	SpanKindClient
	SpanKindServer
	SpanKindProducer
	SpanKindConsumer
)

// Status represents the result status of a span.
type Status int

const (
	StatusUnset Status = iota
	StatusOk
	StatusError
)

type attributeOption struct {
	attributes []Attribute
}

func (o attributeOption) applySpanOption(cfg *spanConfig) {
	cfg.attributes = append(cfg.attributes, o.attributes...)
}

// WithAttributes adds attributes to a span at creation time.
func WithAttributes(attrs ...Attribute) SpanOption {
	return attributeOption{attributes: attrs}
}

type spanKindOption struct {
	kind SpanKind
}

func (o spanKindOption) applySpanOption(cfg *spanConfig) {
	cfg.spanKind = o.kind
}

func WithSpanKind(kind SpanKind) SpanOption {
	return spanKindOption{kind: kind}
}

type timestampOption struct {
	timestamp time.Time
}

func (o timestampOption) applySpanOption(cfg *spanConfig) {
	cfg.timestamp = o.timestamp
}

// WithTimestamp sets the span start time. Defaults to current time if not provided.
func WithTimestamp(t time.Time) SpanOption {
	return timestampOption{timestamp: t}
}

// Attribute helper functions

func Attr(key string, value interface{}) Attribute {
	return Attribute{Key: key, Value: value}
}

func String(key, value string) Attribute {
	return Attribute{Key: key, Value: value}
}

func Int(key string, value int) Attribute {
	return Attribute{Key: key, Value: value}
}

func Int64(key string, value int64) Attribute {
	return Attribute{Key: key, Value: value}
}

func Float64(key string, value float64) Attribute {
	return Attribute{Key: key, Value: value}
}

func Bool(key string, value bool) Attribute {
	return Attribute{Key: key, Value: value}
}
