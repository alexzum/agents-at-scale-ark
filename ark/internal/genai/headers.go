package genai

import (
	"context"
	"fmt"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/client"

	arkv1alpha1 "mckinsey.com/ark/api/v1alpha1"
	arkv1prealpha1 "mckinsey.com/ark/api/v1prealpha1"
)

func ResolveHeaders(ctx context.Context, k8sClient client.Client, headers []arkv1alpha1.Header, namespace string) (map[string]string, error) {
	resolvedHeaders := make(map[string]string)
	for _, header := range headers {
		value, err := ResolveHeaderValue(ctx, k8sClient, header, namespace)
		if err != nil {
			return nil, fmt.Errorf("failed to resolve header %s: %w", header.Name, err)
		}
		resolvedHeaders[header.Name] = value
	}

	return resolvedHeaders, nil
}

func ResolveHeaderValue(ctx context.Context, k8sClient client.Client, header arkv1alpha1.Header, namespace string) (string, error) {
	if header.Value.Value != "" {
		return header.Value.Value, nil
	}

	if header.Value.ValueFrom == nil {
		return "", fmt.Errorf("header value must specify either value or valueFrom.secretKeyRef or valueFrom.configMapKeyRef")
	}

	if header.Value.ValueFrom.SecretKeyRef != nil {
		return resolveHeaderFromSecret(ctx, k8sClient, header.Value.ValueFrom.SecretKeyRef, namespace)
	}

	if header.Value.ValueFrom.ConfigMapKeyRef != nil {
		return resolveHeaderFromConfigMap(ctx, k8sClient, header.Value.ValueFrom.ConfigMapKeyRef, namespace)
	}

	return "", fmt.Errorf("header value must specify either value or valueFrom.secretKeyRef or valueFrom.configMapKeyRef")
}

func resolveHeaderFromSecret(ctx context.Context, k8sClient client.Client, secretRef *corev1.SecretKeySelector, namespace string) (string, error) {
	secret := &corev1.Secret{}
	secretKey := types.NamespacedName{
		Name:      secretRef.Name,
		Namespace: namespace,
	}

	if err := k8sClient.Get(ctx, secretKey, secret); err != nil {
		return "", fmt.Errorf("failed to get secret %s/%s: %w", namespace, secretRef.Name, err)
	}

	value, exists := secret.Data[secretRef.Key]
	if !exists {
		return "", fmt.Errorf("key %s not found in secret %s/%s", secretRef.Key, namespace, secretRef.Name)
	}

	return string(value), nil
}

func resolveHeaderFromConfigMap(ctx context.Context, k8sClient client.Client, configMapRef *corev1.ConfigMapKeySelector, namespace string) (string, error) {
	configMap := &corev1.ConfigMap{}
	configMapKey := types.NamespacedName{
		Name:      configMapRef.Name,
		Namespace: namespace,
	}

	if err := k8sClient.Get(ctx, configMapKey, configMap); err != nil {
		return "", fmt.Errorf("failed to get configMap %s/%s: %w", namespace, configMapRef.Name, err)
	}

	value, exists := configMap.Data[configMapRef.Key]
	if !exists {
		return "", fmt.Errorf("key %s not found in configMap %s/%s", configMapRef.Key, namespace, configMapRef.Name)
	}

	return value, nil
}

func ResolveHeaderValueV1PreAlpha1(ctx context.Context, k8sClient client.Client, header arkv1prealpha1.Header, namespace string) (string, error) {
	v1alpha1Header := arkv1alpha1.Header{
		Name:  header.Name,
		Value: header.Value,
	}
	return ResolveHeaderValue(ctx, k8sClient, v1alpha1Header, namespace)
}
