package genai

import (
	"bytes"
	"context"
	"fmt"
	"text/template"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/client"

	arkv1alpha1 "mckinsey.com/ark/api/v1alpha1"
)

func ResolveQueryInput(ctx context.Context, k8sClient client.Client, namespace, input string, parameters []arkv1alpha1.Parameter) (string, error) {
	if len(parameters) == 0 {
		return input, nil
	}

	templateData, err := resolveQueryParameters(ctx, k8sClient, namespace, parameters)
	if err != nil {
		return "", fmt.Errorf("failed to resolve parameters: %w", err)
	}

	tmpl, err := template.New("query-input").Parse(input)
	if err != nil {
		return "", fmt.Errorf("invalid template syntax in input: %w", err)
	}

	var buf bytes.Buffer
	if err := tmpl.Execute(&buf, templateData); err != nil {
		return "", fmt.Errorf("template execution failed: %w", err)
	}

	return buf.String(), nil
}

func resolveQueryParameters(ctx context.Context, k8sClient client.Client, namespace string, parameters []arkv1alpha1.Parameter) (map[string]string, error) {
	templateData := make(map[string]string)

	for _, param := range parameters {
		if param.Value != "" {
			templateData[param.Name] = param.Value
			continue
		}

		if param.ValueFrom == nil {
			return nil, fmt.Errorf("parameter %s must specify either value or valueFrom", param.Name)
		}

		value, err := resolveQueryValueFrom(ctx, k8sClient, namespace, param.ValueFrom)
		if err != nil {
			return nil, fmt.Errorf("failed to resolve parameter %s: %w", param.Name, err)
		}
		templateData[param.Name] = value
	}

	return templateData, nil
}

func resolveQueryValueFrom(ctx context.Context, k8sClient client.Client, namespace string, valueFrom *arkv1alpha1.ValueFromSource) (string, error) {
	if valueFrom.ConfigMapKeyRef != nil {
		configMap := &corev1.ConfigMap{}
		key := types.NamespacedName{Name: valueFrom.ConfigMapKeyRef.Name, Namespace: namespace}
		if err := k8sClient.Get(ctx, key, configMap); err != nil {
			return "", fmt.Errorf("failed to get ConfigMap %s: %w", valueFrom.ConfigMapKeyRef.Name, err)
		}

		value, exists := configMap.Data[valueFrom.ConfigMapKeyRef.Key]
		if !exists {
			return "", fmt.Errorf("key %s not found in ConfigMap %s", valueFrom.ConfigMapKeyRef.Key, valueFrom.ConfigMapKeyRef.Name)
		}
		return value, nil
	}

	if valueFrom.SecretKeyRef != nil {
		secret := &corev1.Secret{}
		key := types.NamespacedName{Name: valueFrom.SecretKeyRef.Name, Namespace: namespace}
		if err := k8sClient.Get(ctx, key, secret); err != nil {
			return "", fmt.Errorf("failed to get Secret %s: %w", valueFrom.SecretKeyRef.Name, err)
		}

		value, exists := secret.Data[valueFrom.SecretKeyRef.Key]
		if !exists {
			return "", fmt.Errorf("key %s not found in Secret %s", valueFrom.SecretKeyRef.Key, valueFrom.SecretKeyRef.Name)
		}
		return string(value), nil
	}

	return "", fmt.Errorf("no supported valueFrom source specified")
}

// ResolveBodyTemplate resolves body template with parameters and input data
func ResolveBodyTemplate(ctx context.Context, k8sClient client.Client, namespace, bodyTemplate string, parameters []arkv1alpha1.Parameter, inputData map[string]any) (string, error) {
	if bodyTemplate == "" {
		return "", nil
	}

	templateData := make(map[string]any)

	if inputData != nil {
		templateData["input"] = inputData
	}

	if len(parameters) > 0 {
		paramData, err := resolveQueryParameters(ctx, k8sClient, namespace, parameters)
		if err != nil {
			return "", fmt.Errorf("failed to resolve body parameters: %w", err)
		}

		for key, value := range paramData {
			templateData[key] = value
		}
	}

	tmpl, err := template.New("body-template").Parse(bodyTemplate)
	if err != nil {
		return "", fmt.Errorf("invalid template syntax in body: %w", err)
	}

	var buf bytes.Buffer
	if err := tmpl.Execute(&buf, templateData); err != nil {
		return "", fmt.Errorf("body template execution failed: %w", err)
	}

	return buf.String(), nil
}

// GetQueryInputMessages returns a message array based on query type, handling both input and messages
func GetQueryInputMessages(ctx context.Context, query arkv1alpha1.Query, k8sClient client.Client) ([]Message, error) {
	queryType := query.Spec.Type
	if queryType == "" {
		queryType = RoleUser // default type
	}

	if queryType == RoleUser {
		// For 'user' type (default), get input string using helper method
		inputString, err := query.Spec.GetInputString()
		if err != nil {
			return nil, fmt.Errorf("failed to get input string: %w", err)
		}

		// Resolve input with template parameters and create a single user message
		resolvedInput, err := ResolveQueryInput(ctx, k8sClient, query.Namespace, inputString, query.Spec.Parameters)
		if err != nil {
			return nil, fmt.Errorf("failed to resolve query input: %w", err)
		}
		return []Message{NewUserMessage(resolvedInput)}, nil
	} else {
		openaiMessages, err := query.Spec.GetInputMessages()
		if err != nil {
			return nil, fmt.Errorf("failed to get input messages: %w", err)
		}

		messages := make([]Message, len(openaiMessages))
		for i := range openaiMessages {
			messages[i] = Message(openaiMessages[i])
		}
		return messages, nil
	}
}
