variable "aws_region" {
  description = "Primary AWS region"
  type        = string
  default     = "eu-west-1"
}

variable "project_name" {
  description = "Used for naming all resources"
  type        = string
  default     = "pdf-tools"
}

variable "environment" {
  type    = string
  default = "prod"
}

variable "domain_name" {
  description = "Full domain for the site (e.g. pdftools.flairops.cloud)"
  type        = string
  default     = "pdftools.flairops.cloud"
}

variable "app_port" {
  description = "Port the FastAPI container listens on"
  type        = number
  default     = 8000
}

variable "container_cpu" {
  description = "Fargate task CPU units (1024 = 1 vCPU)"
  type        = number
  default     = 512
}

variable "container_memory" {
  description = "Fargate task memory in MiB"
  type        = number
  default     = 2048
}

variable "desired_count" {
  description = "Number of running ECS tasks"
  type        = number
  default     = 1
}

variable "github_repo" {
  description = "GitHub repository in owner/name format, e.g. flairops/pdf-tools"
  type        = string
}

variable "max_upload_mb" {
  description = "Max PDF upload size in MB (passed to the app as an env var)"
  type        = number
  default     = 100
}
