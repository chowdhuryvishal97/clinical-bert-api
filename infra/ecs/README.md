# ECS task definition template

`task-definition.json` is a template used by the GitHub Actions workflow to create a new ECS task definition revision per deploy.

## How it works

- The workflow builds and pushes a Docker image to ECR.
- The workflow injects the new image URI into `task-definition.json` (container `api`).
- The workflow registers a new task definition revision and updates the ECS service.

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

