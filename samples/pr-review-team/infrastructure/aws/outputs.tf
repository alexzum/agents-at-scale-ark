output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_security_group_id" {
  description = "Security group ID for the EKS cluster"
  value       = module.eks.cluster_security_group_id
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data for cluster"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

output "cluster_oidc_provider_arn" {
  description = "ARN of the OIDC provider for the cluster"
  value       = module.eks.oidc_provider_arn
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnets
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnets
}

output "s3_bucket_name" {
  description = "S3 bucket name for PR review logs"
  value       = aws_s3_bucket.pr_reviews.id
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN for PR review logs"
  value       = aws_s3_bucket.pr_reviews.arn
}

output "github_token_secret_arn" {
  description = "ARN of GitHub token secret"
  value       = aws_secretsmanager_secret.github_token.arn
}

output "jira_credentials_secret_arn" {
  description = "ARN of Jira credentials secret"
  value       = aws_secretsmanager_secret.jira_credentials.arn
}

output "model_api_key_secret_arn" {
  description = "ARN of model API key secret"
  value       = aws_secretsmanager_secret.model_api_key.arn
}

output "pr_reviewer_service_role_arn" {
  description = "IAM role ARN for PR reviewer service"
  value       = aws_iam_role.pr_reviewer_service.arn
}

output "configure_kubectl" {
  description = "Command to configure kubectl"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

