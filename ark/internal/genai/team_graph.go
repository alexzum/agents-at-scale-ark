package genai

import (
	"context"
	"fmt"

	corev1 "k8s.io/api/core/v1"
)

func (t *Team) executeGraph(ctx context.Context, userInput Message, history []Message) ([]Message, error) {
	if len(t.Members) == 0 {
		return nil, fmt.Errorf("team %s has no members for graph execution", t.FullName())
	}

	messages := append([]Message{}, history...)
	var newMessages []Message

	memberMap := make(map[string]TeamMember)
	for _, member := range t.Members {
		memberMap[member.GetName()] = member
	}

	// Build adjacency list to support multiple outgoing edges
	transitionMap := make(map[string][]string)
	if t.Graph != nil {
		for _, edge := range t.Graph.Edges {
			transitionMap[edge.From] = append(transitionMap[edge.From], edge.To)
		}
	}

	turnTracker := NewExecutionRecorder(t.Recorder)
	turnTracker.TeamTurn(ctx, "Start", t.FullName(), t.Strategy, 0)

	// Use a queue-based approach to handle multiple outgoing edges
	// This allows for breadth-first traversal of the graph
	visited := make(map[string]bool)
	queue := []string{t.Members[0].GetName()} // Start with first member
	turns := 0

	for len(queue) > 0 {
		// Check maxTurns limit
		if t.MaxTurns != nil && turns >= *t.MaxTurns {
			turnTracker.TeamTurn(ctx, "MaxTurns", t.FullName(), t.Strategy, turns)
			t.Recorder.EmitEvent(ctx, corev1.EventTypeWarning, "TeamMaxTurnsReached", BaseEvent{
				Name: t.FullName(),
				Metadata: map[string]string{
					"strategy": t.Strategy,
					"maxTurns": fmt.Sprintf("%d", *t.MaxTurns),
					"teamName": t.FullName(),
				},
			})
			return newMessages, nil
		}

		// Process current member
		currentMemberName := queue[0]
		queue = queue[1:] // Remove from queue

		// Skip if already visited (prevents infinite loops)
		if visited[currentMemberName] {
			continue
		}
		visited[currentMemberName] = true

		member, exists := memberMap[currentMemberName]
		if !exists {
			return newMessages, fmt.Errorf("member %s not found in team %s", currentMemberName, t.FullName())
		}

		memberTracker := NewExecutionRecorder(t.Recorder)
		memberTracker.ParticipantSelected(ctx, t.FullName(), currentMemberName, "graph")

		if err := t.executeMemberAndAccumulate(ctx, member, userInput, &messages, &newMessages, turns); err != nil {
			if IsTerminateTeam(err) {
				return newMessages, nil
			}
			return newMessages, err
		}

		turns++

		// Add all next members to queue
		nextMembers := transitionMap[currentMemberName]
		for _, nextMemberName := range nextMembers {
			if !visited[nextMemberName] {
				queue = append(queue, nextMemberName)
			}
		}
	}

	return newMessages, nil
}
