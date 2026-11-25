terraform {
  required_version = ">= 1.11.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Configurar bucket, clave y region con backend.hcl (NO versionado).
  # Terraform >= 1.11 permite bloqueo nativo de S3 con use_lockfile = true.
  backend "s3" {}
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "Terraform"
      Milestone   = "Hito3"
    }
  }
}
