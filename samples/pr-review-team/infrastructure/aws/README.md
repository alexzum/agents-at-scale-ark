# ARK PR Review Infrastructure

Terraform configuration for deploying a dedicated EKS cluster for ARK-powered PR reviews.

## Architecture

- EKS cluster with managed node groups
- VPC with public and private subnets
- NAT Gateway for outbound connectivity
- S3 bucket for review logs (90-day retention)
- AWS Secrets Manager for credentials
- IAM roles with IRSA for service accounts

## Prerequisites

- AWS CLI configured
- Terraform >= 1.5
- kubectl
- Helm 3

## Initial Setup

1. Create S3 bucket for Terraform state:
```bash
aws s3 mb s3://ark-pr-review-terraform-state --region us-east-1
aws s3api put-bucket-versioning \
  --bucket ark-pr-review-terraform-state \
  --versioning-configuration Status=Enabled
```

2. Copy and customize variables:
```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your settings
```

3. Store secrets in AWS Secrets Manager:
```bash
# GitHub PAT
aws secretsmanager put-secret-value \
  --secret-id ark-pr-review-github-token \
  --secret-string "ghp_xxxxxxxxxxxxx"

# Jira credentials
aws secretsmanager put-secret-value \
  --secret-id ark-pr-review-jira-credentials \
  --secret-string '{"username":"user@company.com","api_token":"xxx"}'

# Model API key (Azure OpenAI)
aws secretsmanager put-secret-value \
  --secret-id ark-pr-review-model-api-key \
  --secret-string "sk-xxxxxxxxxxxxx"
```

## Deployment

```bash
# Initialize Terraform
terraform init

# Plan changes
terraform plan

# Apply configuration
terraform apply

# Configure kubectl
aws eks update-kubeconfig --region us-east-1 --name ark-pr-review
```

## Network Configuration

### Jira On-Prem Access

If Jira is on-prem, configure network access:

1. **Option A: VPN Connection**
   - Set up AWS Site-to-Site VPN
   - Update route tables
   - Set `jira_cidr_blocks` in terraform.tfvars

2. **Option B: Direct Connect**
   - Establish AWS Direct Connect
   - Configure virtual interfaces
   - Update security groups

3. **Option C: Bastion/Jump Host**
   - Deploy bastion in public subnet
   - Configure SSH tunneling
   - Use SOCKS proxy for Jira access

### Security Groups

Cluster security group allows:
- Outbound HTTPS to GitHub API (0.0.0.0/0:443)
- Outbound HTTPS to Jira (configured CIDR:443)
- Outbound HTTPS to model API endpoints

## Post-Deployment

1. Verify cluster access:
```bash
kubectl get nodes
kubectl get namespaces
```

2. Deploy ARK controller:
```bash
helm install ark-controller ghcr.io/mckinsey/ark/chart \
  --namespace ark-pr-review \
  --create-namespace
```

3. Deploy PR reviewer service (see `services/ark-pr-reviewer/README.md`)

## Maintenance

### Update cluster:
```bash
terraform plan
terraform apply
```

### Scale nodes:
```bash
# Edit terraform.tfvars
node_group_desired_size = 3

terraform apply
```

### Access review logs:
```bash
aws s3 ls s3://ark-pr-review-pr-reviews/

# Download specific review
aws s3 cp s3://ark-pr-review-pr-reviews/agents-at-scale-ark/123/review.json .
```

## Cost Optimization

**Estimated monthly cost (dev environment):**
- EKS Control Plane: $73
- t3.medium nodes (2x): ~$60
- NAT Gateway: ~$32
- S3 storage: ~$1
- **Total: ~$166/month**

**Prod environment recommendations:**
- Use Spot instances for workers
- Multiple NAT gateways in prod
- Increase node sizes for performance
- Enable cluster autoscaling

## Troubleshooting

### Cannot connect to cluster:
```bash
aws eks update-kubeconfig --region us-east-1 --name ark-pr-review
kubectl cluster-info
```

### Cannot access Jira:
```bash
# Test from pod
kubectl run -it --rm debug --image=alpine --restart=Never -- sh
apk add curl
curl -I https://jira.company.com
```

### Review logs not appearing:
```bash
# Check IAM role permissions
kubectl describe sa ark-pr-reviewer -n ark-pr-review

# Check pod logs
kubectl logs -n ark-pr-review deployment/ark-pr-reviewer
```

## Cleanup

```bash
# Destroy infrastructure
terraform destroy

# Delete S3 state bucket
aws s3 rb s3://ark-pr-review-terraform-state --force
```

