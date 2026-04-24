# Terraform (AWS ECS + ALB)

This directory provisions long-lived AWS infrastructure for the API:

- VPC + public/private subnets + NAT
- ALB + target group + listener
- ECR repository
- ECS cluster + Fargate service
- IAM roles (ECS task execution + GitHub Actions OIDC deploy role)

## Prerequisites

- Terraform \(>= 1.5\)
- AWS credentials with permissions to create the above resources

## Inputs

Required:
- `github_repo`: GitHub repository in `owner/name` format used in the OIDC trust policy

Optional:
- `aws_region` (default `us-east-1`)
- `env` (default `dev`)
- `project_name` (default `clinical-bert`)
- `cpu`, `memory`, `desired_count`, `container_port`
- `github_ref_pattern` (optional override for the GitHub OIDC subject condition)

## Typical commands

```bash
terraform init

terraform plan \
  -var="github_repo=OWNER/REPO" \
  -var="env=dev"

terraform apply \
  -var="github_repo=OWNER/REPO" \
  -var="env=dev"
```

## Outputs (used by deployments)

Key outputs:
- `github_actions_role_arn`: put this into GitHub Secret `AWS_ROLE_TO_ASSUME`
- `ecs_cluster_name`: put this into GitHub Variable `ECS_CLUSTER`
- `ecs_service_name`: put this into GitHub Variable `ECS_SERVICE`
- `ecr_repository_url`: derive `ECR_REPOSITORY` from the last path segment (repository name)
- `alb_dns_name`: service entrypoint for `/health` and `/predict`
- `task_execution_role_arn`: used in `infra/ecs/task-definition.json`

## Notes

- The ECS service includes `lifecycle.ignore_changes = [task_definition]` so Terraform does not fight CI/CD deployments.
- The VPC is intentionally minimal for a single service. For production, prefer a shared networking module and more explicit AZ handling.

