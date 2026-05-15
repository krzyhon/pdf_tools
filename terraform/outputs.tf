output "nameservers" {
  description = "Add these as NS records for pdftools.flairops.cloud at your external DNS provider (one-time step)"
  value       = aws_route53_zone.subdomain.name_servers
}

output "site_url" {
  description = "Public URL of the site"
  value       = "https://${var.domain_name}"
}

output "cloudfront_distribution_id" {
  description = "Needed for cache invalidations after frontend deploys"
  value       = aws_cloudfront_distribution.main.id
}

output "ecr_repository_url" {
  description = "Push Docker images here: docker push <url>:latest"
  value       = aws_ecr_repository.app.repository_url
}

output "frontend_bucket" {
  description = "Sync static files here: aws s3 sync dist/ s3://<bucket>"
  value       = aws_s3_bucket.frontend.id
}

output "temp_files_bucket" {
  value = aws_s3_bucket.temp_files.id
}

output "alb_dns_name" {
  description = "ALB hostname (for debugging — direct access is blocked by the secret header)"
  value       = aws_lb.main.dns_name
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "github_actions_role_arn" {
  description = "Set this as the AWS_DEPLOY_ROLE_ARN secret in your GitHub repository"
  value       = aws_iam_role.github_actions.arn
}

output "terraform_role_arn" {
  description = "Set this as the AWS_TERRAFORM_ROLE_ARN secret in your GitHub repository"
  value       = aws_iam_role.terraform.arn
}
