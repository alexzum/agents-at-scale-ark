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

	memberMap := t.buildMemberMap()
	transitionMap := t.buildTransitionMap()

	turnTracker := NewExecutionRecorder(t.Recorder)
	turnTracker.TeamTurn(ctx, "Start", t.FullName(), t.Strategy, 0)

	visited := make(map[string]bool)
	queue := []string{t.Members[0].GetName()}
	turns := 0

	for len(queue) > 0 {
		if t.checkMaxTurnsReached(ctx, turns, turnTracker) {
			return newMessages, nil
		}

		currentMemberName, queue := t.processNextMember(queue, visited, memberMap)
		if currentMemberName == "" {
			continue
		}

		memberTracker := NewExecutionRecorder(t.Recorder)
		memberTracker.ParticipantSelected(ctx, t.FullName(), currentMemberName, "graph")

		if err := t.executeMemberAndAccumulate(ctx, memberMap[currentMemberName], userInput, &messages, &newMessages, turns); err != nil {
			if IsTerminateTeam(err) {
				return newMessages, nil
			}
			return newMessages, err
		}

		turns++
		t.addNextMembersToQueue(&queue, transitionMap, currentMemberName, visited)
	}

	return newMessages, nil
}

func (t *Team) buildMemberMap() map[string]TeamMember {
	memberMap := make(map[string]TeamMember)
	for _, member := range t.Members {
		memberMap[member.GetName()] = member
	}
	return memberMap
}

func (t *Team) buildTransitionMap() map[string][]string {
	transitionMap := make(map[string][]string)
	if t.Graph != nil {
		for _, edge := range t.Graph.Edges {
			transitionMap[edge.From] = append(transitionMap[edge.From], edge.To)
		}
	}
	return transitionMap
}

func (t *Team) checkMaxTurnsReached(ctx context.Context, turns int, turnTracker *ExecutionRecorder) bool {
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
		return true
	}
	return false
}

func (t *Team) processNextMember(queue []string, visited map[string]bool, memberMap map[string]TeamMember) (string, []string) {
	currentMemberName := queue[0]
	queue = queue[1:]

	if visited[currentMemberName] {
		return "", queue
	}
	visited[currentMemberName] = true

	if _, exists := memberMap[currentMemberName]; !exists {
		return "", queue
	}

	return currentMemberName, queue
}

func (t *Team) addNextMembersToQueue(queue *[]string, transitionMap map[string][]string, currentMemberName string, visited map[string]bool) {
	nextMembers := transitionMap[currentMemberName]
	for _, nextMemberName := range nextMembers {
		if !visited[nextMemberName] {
			*queue = append(*queue, nextMemberName)
		}
	}
}
