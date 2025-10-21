/* Copyright 2025. McKinsey & Company */

package telemetry

import (
	"context"
)

// QueryRecorder provides domain-specific telemetry for query execution.
// Encapsulates query lifecycle tracing with consistent attribute naming.
type QueryRecorder interface {
	// StartQuery begins tracing a query execution.
	StartQuery(ctx context.Context, queryName, queryNamespace, phase string) (context.Context, Span)

	// StartTarget begins tracing a specific query target (agent, team, model, tool).
	StartTarget(ctx context.Context, targetType, targetName string) (context.Context, Span)

	// RecordInput sets the input content on a span.
	RecordInput(span Span, content string)

	// RecordOutput sets the output content on a span.
	RecordOutput(span Span, content string)

	// RecordMessages records input messages for multi-turn conversations.
	RecordMessages(span Span, messages []string)

	// RecordTokenUsage records LLM token consumption.
	RecordTokenUsage(span Span, promptTokens, completionTokens, totalTokens int64)

	// RecordModelDetails records model provider and configuration.
	RecordModelDetails(span Span, modelName, provider, modelType string)

	// RecordSessionID associates a span with a session for multi-query tracking.
	RecordSessionID(span Span, sessionID string)

	// RecordSuccess marks a span as successfully completed.
	RecordSuccess(span Span)

	// RecordError marks a span as failed with error details.
	RecordError(span Span, err error)
}

// Standardized attribute keys for ARK telemetry.
// Following OpenTelemetry semantic conventions where applicable.
const (
	// Query attributes
	AttrQueryName      = "query.name"
	AttrQueryNamespace = "query.namespace"
	AttrQueryPhase     = "query.phase"
	AttrQueryInput     = "query.input"
	AttrQueryOutput    = "query.output"

	// Target attributes
	AttrTargetType = "target.type"
	AttrTargetName = "target.name"

	// Agent attributes
	AttrAgentName = "agent.name"

	// Team attributes
	AttrTeamName = "team.name"

	// Model attributes (aligned with OpenTelemetry GenAI conventions)
	AttrModelName     = "llm.model.name"
	AttrModelProvider = "llm.model.provider"
	AttrModelType     = "llm.model.type"

	// Token usage (aligned with OpenTelemetry GenAI conventions)
	AttrTokensPrompt     = "gen_ai.usage.input_tokens"
	AttrTokensCompletion = "gen_ai.usage.output_tokens"
	AttrTokensTotal      = "gen_ai.usage.total_tokens"

	// Langfuse-specific attributes for compatibility
	AttrLangfuseModel    = "model"
	AttrLangfuseProvider = "provider"
	AttrLangfuseType     = "type"

	// Session tracking
	AttrSessionID = "session.id"

	// Tool attributes
	AttrToolName        = "tool.name"
	AttrToolType        = "tool.type"
	AttrToolInput       = "tool.input"
	AttrToolOutput      = "tool.output"
	AttrToolDescription = "tool.description"

	// Message attributes
	AttrMessagesInputCount = "messages.input_count"
	AttrMessagesInput      = "messages.input"
	AttrMessagesOutput     = "messages.output"

	// Service attributes
	AttrServiceName    = "service.name"
	AttrServiceVersion = "service.version"
	AttrComponentName  = "component"

	// Finish reason (aligned with OpenTelemetry GenAI conventions)
	AttrFinishReason = "gen_ai.completion.finish_reason"
)

// Target types for query execution
const (
	TargetTypeAgent = "agent"
	TargetTypeTeam  = "team"
	TargetTypeModel = "model"
	TargetTypeTool  = "tool"
)

// Langfuse observation types for compatibility
const (
	ObservationTypeAgent      = "agent"
	ObservationTypeGeneration = "generation"
	ObservationTypeTool       = "tool"
)
