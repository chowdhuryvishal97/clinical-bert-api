output "ecr_repository_url" {
  value       = aws_ecr_repository.app.repository_url
  description = "ECR repository URL to push images to."
}

output "ecs_cluster_name" {
  value       = aws_ecs_cluster.this.name
  description = "ECS cluster name."
}

output "ecs_service_name" {
  value       = aws_ecs_service.api.name
  description = "ECS service name."
}

output "alb_dns_name" {
  value       = aws_lb.this.dns_name
  description = "ALB DNS name."
}

output "github_actions_role_arn" {
  value       = aws_iam_role.github_deploy.arn
  description = "Role ARN to assume from GitHub Actions via OIDC."
}

output "task_execution_role_arn" {
  value       = aws_iam_role.ecs_task_execution.arn
  description = "ECS task execution role ARN."
}

