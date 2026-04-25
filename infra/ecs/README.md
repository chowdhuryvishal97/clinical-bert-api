# ECS task definition template

`task-definition.json` is a template used by the GitHub Actions workflow to create a new ECS task definition revision per deploy.

## How it works

- The workflow builds and pushes a Docker image to ECR.
- The workflow injects the new image URI into `task-definition.json` (container `api`).
- The workflow registers a new task definition revision and updates the ECS service.

## Bootstrap (first deploy)

Terraform creates an ECS service that initially references the image tag `:initial` in ECR. Before the service can come up cleanly the first time, make sure **an image exists in ECR** with that tag, either by:

- Running the GitHub Actions deploy workflow once (after configuring required secrets/vars), or
- Manually building and pushing an `initial` image (see `infra/terraform/README.md` for commands).

## One-time setup

Update `task-definition.json` placeholders:

- `family`: must match the Terraform task definition family  
  Format: `${project_name}-${env}-api`
- `executionRoleArn`: Terraform output `task_execution_role_arn`
- `awslogs-group`: Terraform log group name  
  Format: `/ecs/${project_name}-${env}`
- `awslogs-region`: AWS region (same as Terraform `aws_region`)

The `image` field value is replaced automatically during deploys.

## Container name

The workflow expects the container name to be `api` \(matches Terraform and the template\).

