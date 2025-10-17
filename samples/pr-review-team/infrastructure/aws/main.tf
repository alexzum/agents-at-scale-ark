terraform {
  required_version = ">= 1.5"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }
  
  backend "s3" {
    bucket = "ark-pr-review-terraform-state"
    key    = "terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "ARK-PR-Review"
      ManagedBy   = "Terraform"
      Environment = var.environment
    }
  }
}

data "aws_availability_zones" "available" {
  state = "available"
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  
  name = "${var.cluster_name}-vpc"
  cidr = var.vpc_cidr
  
  azs             = slice(data.aws_availability_zones.available.names, 0, 3)
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs
  
  enable_nat_gateway   = true
  single_nat_gateway   = var.environment == "dev"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }
  
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"
  
  cluster_name    = var.cluster_name
  cluster_version = var.kubernetes_version
  
  vpc_id                   = module.vpc.vpc_id
  subnet_ids               = module.vpc.private_subnets
  control_plane_subnet_ids = module.vpc.private_subnets
  
  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true
  
  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }
  
  eks_managed_node_groups = {
    default = {
      name = "${var.cluster_name}-node-group"
      
      instance_types = var.node_instance_types
      capacity_type  = "ON_DEMAND"
      
      min_size     = var.node_group_min_size
      max_size     = var.node_group_max_size
      desired_size = var.node_group_desired_size
      
      disk_size = 50
      
      labels = {
        Environment = var.environment
        NodeGroup   = "default"
      }
      
      tags = {
        NodeGroup = "default"
      }
    }
  }
  
  manage_aws_auth_configmap = true
  aws_auth_roles = var.additional_aws_auth_roles
  aws_auth_users = var.additional_aws_auth_users
}

resource "aws_security_group_rule" "cluster_to_jira" {
  count = var.jira_cidr_blocks != null ? 1 : 0
  
  description       = "Allow cluster to access Jira on-prem"
  type              = "egress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = var.jira_cidr_blocks
  security_group_id = module.eks.cluster_security_group_id
}

resource "aws_security_group_rule" "cluster_to_github" {
  description       = "Allow cluster to access GitHub API"
  type              = "egress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = module.eks.cluster_security_group_id
}

resource "aws_s3_bucket" "pr_reviews" {
  bucket = "${var.cluster_name}-pr-reviews"
}

resource "aws_s3_bucket_lifecycle_configuration" "pr_reviews" {
  bucket = aws_s3_bucket.pr_reviews.id
  
  rule {
    id     = "delete-old-reviews"
    status = "Enabled"
    
    expiration {
      days = var.review_log_retention_days
    }
  }
}

resource "aws_s3_bucket_versioning" "pr_reviews" {
  bucket = aws_s3_bucket.pr_reviews.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "pr_reviews" {
  bucket = aws_s3_bucket.pr_reviews.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_secretsmanager_secret" "github_token" {
  name        = "${var.cluster_name}-github-token"
  description = "GitHub PAT for PR review access"
}

resource "aws_secretsmanager_secret" "jira_credentials" {
  name        = "${var.cluster_name}-jira-credentials"
  description = "Jira API credentials for ticket access"
}

resource "aws_secretsmanager_secret" "model_api_key" {
  name        = "${var.cluster_name}-model-api-key"
  description = "API key for LLM model provider"
}

resource "aws_iam_policy" "pr_reviewer_service" {
  name        = "${var.cluster_name}-pr-reviewer-service"
  description = "IAM policy for ARK PR reviewer service"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.pr_reviews.arn,
          "${aws_s3_bucket.pr_reviews.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.github_token.arn,
          aws_secretsmanager_secret.jira_credentials.arn,
          aws_secretsmanager_secret.model_api_key.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role" "pr_reviewer_service" {
  name = "${var.cluster_name}-pr-reviewer-service"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = module.eks.oidc_provider_arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "${module.eks.oidc_provider}:sub" = "system:serviceaccount:ark-pr-review:ark-pr-reviewer"
            "${module.eks.oidc_provider}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "pr_reviewer_service" {
  role       = aws_iam_role.pr_reviewer_service.name
  policy_arn = aws_iam_policy.pr_reviewer_service.arn
}

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
  }
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
    }
  }
}

resource "kubernetes_namespace" "ark_pr_review" {
  metadata {
    name = "ark-pr-review"
    labels = {
      name = "ark-pr-review"
    }
  }
}

resource "kubernetes_service_account" "ark_pr_reviewer" {
  metadata {
    name      = "ark-pr-reviewer"
    namespace = kubernetes_namespace.ark_pr_review.metadata[0].name
    annotations = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.pr_reviewer_service.arn
    }
  }
}

