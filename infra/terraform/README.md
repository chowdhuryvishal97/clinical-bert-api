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
- `github_ref_pattern` (optional override for the GitHub OIDC subject condition; if unset, defaults to the branches used by the GitHub Actions workflow triggers)

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

## First-time deploy (important: `:initial` image)

This Terraform config creates an ECS task definition that references an **ECR image tag named `initial`**:

- Container image is set to: `<ecr_repository_url>:initial`

If that tag does not exist yet, the ECS service will fail to start because tasks cannot pull the image.

### Recommended bootstrap sequence

1) Create the ECR repository (and other infra if you want), then push an `initial` image.

- Option A: Apply everything (service may fail until the image exists), then push the image, then apply again.
- Option B (cleaner): Create ECR first, push `initial`, then apply the rest.

Example (Option B):

```bash
terraform init

# 1) Create ECR repo first
terraform apply \
  -target=aws_ecr_repository.app \
  -var="github_repo=OWNER/REPO" \
  -var="env=dev"

# 2) Build & push an image tagged `initial` (see below)

# 3) Create/finish the rest of the infrastructure
terraform apply \
  -var="github_repo=OWNER/REPO" \
  -var="env=dev"
```

### Windows / PowerShell note (quoting `-target`)

On Windows PowerShell, quote the `-target` value to avoid argument parsing issues:

```powershell
terraform apply -target="aws_ecr_repository.app" -var="github_repo=OWNER/REPO" -var="env=dev"
```

### Pushing the `initial` image

This repo’s Dockerfile lives at `api/Dockerfile`, and the build context should be the `api/` directory.

Build and push from the repo root. Replace placeholders:

```bash
# Set these for your account/region
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012
ECR_REPO_NAME=clinical-bert-dev-api   # example: "${project_name}-${env}-api"

aws ecr get-login-password --region "$AWS_REGION" | \
  docker login --username AWS --password-stdin \
  "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

docker build -t "$ECR_REPO_NAME:initial" -f api/Dockerfile api
docker tag "$ECR_REPO_NAME:initial" \
  "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:initial"
docker push \
  "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:initial"
```

PowerShell (Windows) equivalent:

```powershell
# Run from the repo root (Dockerfile is in api/Dockerfile)
Set-Location S:\projects\mlops\clinical-bert-api

$env:AWS_REGION="us-east-1"
$env:AWS_ACCOUNT_ID="123456789012"
$env:ECR_REPO_NAME="clinical-bert-dev-api"  # "${project_name}-${env}-api"

# Login to ECR (this form worked reliably on Windows PowerShell)
$pw = aws ecr get-login-password --region $env:AWS_REGION
docker login --username AWS --password $pw "$env:AWS_ACCOUNT_ID.dkr.ecr.$env:AWS_REGION.amazonaws.com"

docker build -t "${env:ECR_REPO_NAME}:initial" ./api
docker tag "${env:ECR_REPO_NAME}:initial" "${env:AWS_ACCOUNT_ID}.dkr.ecr.${env:AWS_REGION}.amazonaws.com/${env:ECR_REPO_NAME}:initial"
docker push "${env:AWS_ACCOUNT_ID}.dkr.ecr.${env:AWS_REGION}.amazonaws.com/${env:ECR_REPO_NAME}:initial"
```

If you must run the build from a different directory, point Docker at the repo-root `Dockerfile` and build context explicitly:

```powershell
# Example: run from infra/terraform but build using repo root as context
docker build -t "$env:ECR_REPO_NAME:initial" -f ..\..\api\Dockerfile ..\..\api
```

Note: Docker may warn that `--password` is insecure and recommend `--password-stdin`. If you prefer `--password-stdin`, you can try:

```powershell
aws ecr get-login-password --region $env:AWS_REGION |
  docker login --username AWS --password-stdin "$env:AWS_ACCOUNT_ID.dkr.ecr.$env:AWS_REGION.amazonaws.com"
```

On some Windows setups this piped form can fail even when credentials are correct; use the `$pw = ...` variant above if that happens.

Notes:

- The ECR repository **URI** is exposed as output `ecr_repository_url`.
- The repository **name** is the last path segment of that URL (used by many CI variables).

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

