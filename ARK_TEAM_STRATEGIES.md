# ARK Team Execution Strategies

This document explains how messages flow between agents in ARK teams and details all available team execution strategies.

## Overview

ARK supports multiple team execution strategies that define how agents coordinate and process messages. Each strategy implements different patterns for multi-agent collaboration, from simple pipelines to AI-driven dynamic selection.

## Message Flow Architecture

### Core Components

1. **Query Controller**: Orchestrates team execution via `executeTeam()` in `query_controller.go`
2. **Team Object**: Contains members, strategy, and execution context
3. **Message Accumulation**: Shared context passed between agents
4. **Agent Execution**: Individual agent processing with full conversation history

### Technical Implementation

```go
// From team.go - Core execution pattern
func (t *Team) Execute(ctx context.Context, userInput Message, history []Message) ([]Message, error) {
    var execFunc func(context.Context, Message, []Message) ([]Message, error)
    switch t.Strategy {
    case "sequential":
        execFunc = t.executeSequential
    case "round-robin":
        execFunc = t.executeRoundRobin
    case "selector":
        execFunc = t.executeSelector
    case "graph":
        execFunc = t.executeGraph
    }
    return t.executeWithTracking(teamTracker, execFunc, ctx, userInput, history)
}
```

### Message Accumulation Pattern

All strategies use the same message accumulation mechanism:

```go
// From team.go:207-234
func (t *Team) executeMemberAndAccumulate(ctx context.Context, member TeamMember, userInput Message, messages, newMessages *[]Message, turn int) error {
    memberNewMessages, err := member.Execute(ctx, userInput, *messages)
    
    // Accumulate responses into shared context
    *messages = append(*messages, memberNewMessages...)      // For next agent
    *newMessages = append(*newMessages, memberNewMessages...) // For final response
}
```

## Team Execution Strategies

### 1. Sequential Strategy

**Flow Pattern**: Linear pipeline execution
```
Agent 1 → Agent 2 → Agent 3 → Done
```

#### Configuration
```yaml
apiVersion: ark.mckinsey.com/v1alpha1
kind: Team
metadata:
  name: sequential-team
spec:
  strategy: sequential
  members:
  - name: inquiry-router
    type: agent
  - name: account-helper
    type: agent  
  - name: loan-advisor
    type: agent
```

#### Technical Implementation
```go
// From team.go:64-82
func (t *Team) executeSequential(ctx context.Context, userInput Message, history []Message) ([]Message, error) {
    messages := slices.Clone(history)
    var newMessages []Message

    for i, member := range t.Members {
        if err := t.executeMemberAndAccumulate(ctx, member, userInput, &messages, &newMessages, i); err != nil {
            if IsTerminateTeam(err) {
                return newMessages, nil
            }
            return newMessages, err
        }
    }
    return newMessages, nil
}
```

#### Message Flow Example (Banking Demo)
1. **User Input**: "What's my account balance and what loans do you offer?"
2. **Inquiry Router**: Classifies as `"mixed"` request → Added to message history
3. **Account Helper**: Receives user input + router classification → Processes account portion → Adds response to history
4. **Loan Advisor**: Receives user input + router + account responses → Processes loan portion → Final comprehensive response

#### Characteristics
- **Execution**: One-time pass through all members in defined order
- **Message History**: Each agent receives accumulated responses from all previous agents
- **Termination**: Completes after all members execute once
- **Use Cases**: Pipeline workflows, document processing chains, structured analysis

---

### 2. Round-Robin Strategy

**Flow Pattern**: Continuous cycling through all members
```
Agent A → Agent B → Agent C → Agent A → Agent B → ... (until maxTurns)
```

#### Configuration
```yaml
apiVersion: ark.mckinsey.com/v1alpha1
kind: Team
metadata:
  name: roundrobin-team
spec:
  strategy: round-robin
  maxTurns: 3
  members:
  - name: agent-a
    type: agent
  - name: agent-b
    type: agent
  - name: agent-c
    type: agent
```

#### Technical Implementation
```go
// From team.go:85-116
func (t *Team) executeRoundRobin(ctx context.Context, userInput Message, history []Message) ([]Message, error) {
    messages := slices.Clone(history)
    var newMessages []Message

    for turn := 0; ; turn++ {
        turnTracker := NewExecutionRecorder(t.Recorder)
        turnTracker.TeamTurn(ctx, "Start", t.FullName(), t.Strategy, turn)

        for i, member := range t.Members {
            if err := t.executeMemberAndAccumulate(ctx, member, userInput, &messages, &newMessages, i); err != nil {
                if IsTerminateTeam(err) {
                    return newMessages, nil
                }
                return newMessages, err
            }
        }

        if t.MaxTurns != nil && turn+1 >= *t.MaxTurns {
            return newMessages, fmt.Errorf("team round-robin MaxTurns reached %s", t.GetName())
        }
    }
}
```

#### Characteristics
- **Execution**: Cycles through all members repeatedly
- **Message History**: Each agent gets full conversation history including previous cycles
- **Termination**: Requires `maxTurns` to prevent infinite loops, or `terminate` tool
- **Use Cases**: Collaborative discussions, iterative refinement, brainstorming sessions
- **Turn Tracking**: Maintains turn counter and logs each cycle

---

### 3. Selector Strategy

**Flow Pattern**: AI model dynamically selects next participant
```
Input → AI Selector → Chosen Agent → AI Selector → Next Agent → ...
```

#### Configuration
```yaml
apiVersion: ark.mckinsey.com/v1alpha1
kind: Team
metadata:
  name: selector-team
spec:
  strategy: selector
  maxTurns: 10
  selector:
    model: gpt-4
    selectorPrompt: |
      Choose the best participant for the next response based on conversation context.
      Available: {{.Participants}}
      History: {{.History}}
  members:
  - name: researcher
    type: agent
  - name: analyst
    type: agent
  - name: writer
    type: agent
```

#### Technical Implementation
```go
// From team_selector.go:58-114
func (t *Team) selectMember(ctx context.Context, messages []Message, tmpl *template.Template, participantsList, rolesList, previousMember string) (TeamMember, int, error) {
    history := buildHistory(messages)
    data := SelectorTemplateData{
        Roles:        rolesList,
        Participants: participantsList,
        History:      history,
    }

    var buf bytes.Buffer
    tmpl.Execute(&buf, data)

    model, err := LoadModel(ctx, t.Client, t.Selector, t.Namespace)
    selectorMessages := []Message{
        NewSystemMessage(buf.String()),
        NewUserMessage("Select the next participant to respond."),
    }

    response, err := model.ChatCompletion(ctx, selectorMessages, nil)
    selectedName := strings.TrimSpace(response.Choices[0].Message.Content)

    // Find selected member or fallback to first member
    for i, member := range t.Members {
        if member.GetName() == selectedName {
            return member, i, nil
        }
    }
    return t.Members[0], 0, nil // Fallback
}
```

#### Template Variables
- `{{.Participants}}`: Comma-separated member names
- `{{.Roles}}`: Member names with descriptions  
- `{{.History}}`: Formatted conversation history

#### Characteristics
- **Execution**: AI model chooses next participant based on conversation context
- **Message History**: Selected agent receives full conversation history
- **Termination**: `maxTurns` required + agents can use `terminate` tool
- **Fallback**: Defaults to first member if selection fails
- **Anti-repetition**: Prevents consecutive execution by same member
- **Use Cases**: Complex workflows where expertise needs depend on context

---

### 4. Graph Strategy

**Flow Pattern**: Directed workflow following defined edges
```
Researcher → Analyzer → Reviewer → Writer (predefined transitions)
```

#### Configuration
```yaml
apiVersion: ark.mckinsey.com/v1alpha1
kind: Team
metadata:
  name: graph-team
spec:
  strategy: graph
  maxTurns: 5
  members:
  - name: researcher
    type: agent
  - name: analyzer
    type: agent
  - name: reviewer
    type: agent
  - name: writer
    type: agent
  graph:
    edges:
    - from: researcher
      to: analyzer
    - from: analyzer
      to: reviewer
    - from: reviewer
      to: writer
```

#### Technical Implementation
```go
// From team_graph.go:8-62
func (t *Team) executeGraph(ctx context.Context, userInput Message, history []Message) ([]Message, error) {
    messages := append([]Message{}, history...)
    var newMessages []Message

    memberMap := make(map[string]TeamMember)
    for _, member := range t.Members {
        memberMap[member.GetName()] = member
    }

    transitionMap := make(map[string]string)
    if t.Graph != nil {
        for _, edge := range t.Graph.Edges {
            transitionMap[edge.From] = edge.To
        }
    }

    currentMemberName := t.Members[0].GetName()

    for turns := 0; ; turns++ {
        member := memberMap[currentMemberName]
        
        if err := t.executeMemberAndAccumulate(ctx, member, userInput, &messages, &newMessages, turns); err != nil {
            if IsTerminateTeam(err) {
                return newMessages, nil
            }
            return newMessages, err
        }

        nextMember := transitionMap[currentMemberName]
        if nextMember == "" {
            break // No outgoing edge = end execution
        }
        currentMemberName = nextMember

        if t.MaxTurns != nil && turns+1 >= *t.MaxTurns {
            return newMessages, fmt.Errorf("team graph MaxTurns reached")
        }
    }
    return newMessages, nil
}
```

#### Validation Rules
```go
// From team_webhook.go:158-186
func (v *TeamCustomValidator) validateGraphStrategy(team *arkv1alpha1.Team) error {
    // Each member can have max 1 outgoing edge
    transitionMap := make(map[string]bool)
    for i, edge := range team.Spec.Graph.Edges {
        if _, exists := transitionMap[edge.From]; exists {
            return fmt.Errorf("member '%s' has more than one outgoing edge", edge.From)
        }
        transitionMap[edge.From] = true
    }
    return nil
}
```

#### Characteristics
- **Execution**: Follows predefined directed edges between agents
- **Message History**: Each agent gets accumulated history as it progresses through graph
- **Termination**: Ends when no outgoing edge exists + `maxTurns` safety limit
- **Constraints**: Each member can have maximum 1 outgoing edge
- **Start Point**: Always begins with first member in members array
- **Use Cases**: Fixed workflows, approval chains, quality control pipelines

---

## Strategy Comparison

| Strategy | Execution Pattern | Termination | Configuration Required | Use Cases |
|----------|------------------|-------------|----------------------|-----------|
| **Sequential** | Linear pipeline | After all members execute once | `members` | Document processing, structured analysis |
| **Round-Robin** | Continuous cycles | `maxTurns` or `terminate` tool | `members` + `maxTurns` | Collaborative discussions, iterative work |
| **Selector** | AI-driven selection | `maxTurns` or `terminate` tool | `members` + `maxTurns` + `selector` config | Context-dependent expertise routing |
| **Graph** | Directed workflow | No outgoing edge or `maxTurns` | `members` + `maxTurns` + `graph.edges` | Fixed workflows, approval processes |

## Advanced Features

### Nested Teams
All strategies support teams as members:
```yaml
spec:
  members:
  - name: sub-team
    type: team
  - name: agent1
    type: agent
```

### Early Termination
Agents can end team execution early using the terminate tool:
```yaml
apiVersion: ark.mckinsey.com/v1alpha1
kind: Agent
metadata:
  name: coordinator
spec:
  prompt: "Use terminate tool when task is complete."
  tools:
  - name: terminate
    type: built-in
```

### Error Handling
- Message history preserved on errors
- Graceful termination via `TerminateTeam` error
- Turn tracking and limits for safety
- Event recording for observability

## Banking Demo Example

The current banking demo uses **sequential strategy**:

```yaml
# demo-resources/teams/customer-service-team.yaml
apiVersion: ark.mckinsey.com/v1alpha1
kind: Team
metadata:
  name: customer-service-team
  namespace: demo-bank
spec:
  strategy: "sequential"
  members:
    - name: inquiry-router
      type: agent
    - name: account-helper
      type: agent  
    - name: loan-advisor
      type: agent
```

**Why Sequential for Banking Demo?**
- **Predictable Flow**: Router → Account Helper → Loan Advisor
- **Comprehensive Coverage**: Every specialized agent contributes to complex queries
- **Context Building**: Each agent builds on previous agent's classification/analysis
- **Demo Reliability**: Consistent, predictable responses for live demonstrations

**Alternative Strategies for Banking:**
- **Selector**: AI routes based on query complexity ("simple balance" → Account Helper only)
- **Graph**: Approval workflow (Router → Account → Risk Assessment → Loan → Manager)
- **Round-Robin**: Iterative customer service discussion with multiple specialists

## Implementation Files

- **Core Team Logic**: `ark/internal/genai/team.go`
- **Sequential Strategy**: `ark/internal/genai/team.go:64-82`
- **Round-Robin Strategy**: `ark/internal/genai/team.go:85-116`
- **Selector Strategy**: `ark/internal/genai/team_selector.go`
- **Graph Strategy**: `ark/internal/genai/team_graph.go`
- **Query Controller**: `ark/internal/controller/query_controller.go:584-621`
- **Validation**: `ark/internal/webhook/v1/team_webhook.go`

## Sample Files

- **Sequential**: `samples/teams/sequential.yaml`
- **Graph Workflow**: `samples/teams/graph-strategy.yaml`
- **Selector Strategy**: `samples/teams/selector-strategy.yaml`
- **Banking Demo**: `demo-resources/teams/customer-service-team.yaml`
