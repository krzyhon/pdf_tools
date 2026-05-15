terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

  # Uncomment after creating the state bucket (one-time bootstrap):
  #   aws s3 mb s3://pdf-tools-tfstate-<account-id> --region eu-west-1
  # backend "s3" {
  #   bucket       = "pdf-tools-tfstate-<account-id>"
  #   key          = "pdf-tools/terraform.tfstate"
  #   region       = "eu-west-1"
  #   use_lockfile = true   # native S3 locking — no DynamoDB needed (requires Terraform >= 1.10)
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# CloudFront ACM certificates must live in us-east-1
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
