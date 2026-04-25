variable "project_name" {
  type        = string
  description = "Name prefix for AWS resources."
  default     = "clinical-bert"
}

variable "aws_region" {
  type        = string
  description = "AWS region."
  default     = "us-east-1"
}

variable "env" {
  type        = string
  description = "Environment name (e.g. dev/stage/prod)."
  default     = "dev"
}

variable "container_port" {
  type        = number
  description = "Container port exposed by the API."
  default     = 8080
}

variable "cpu" {
  type        = number
  description = "Fargate CPU units."
  default     = 1024
}

variable "memory" {
  type        = number
  description = "Fargate memory (MiB)."
  default     = 2048
}

variable "desired_count" {
  type        = number
  description = "Desired ECS task count."
  default     = 1
}

variable "github_repo" {
  type        = string
  description = "GitHub repo in owner/name form used for OIDC trust policy (e.g. org/repo)."
  default     = "chowdhuryvishal97/clinical-bert-api"
}

variable "github_ref_pattern" {
  type        = string
  description = "Allowed GitHub OIDC subject pattern (e.g. repo:org/repo:ref:refs/heads/main or repo:org/repo:ref:refs/heads/*). If empty, Terraform will allow the branches used by the workflow triggers."
  default     = ""
}

