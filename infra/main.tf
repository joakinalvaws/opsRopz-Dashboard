terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend remoto. Crear el bucket y la tabla de locks una sola vez (manual o
  # con un workspace de bootstrap) antes del primer `terraform init`.
  backend "s3" {
    bucket         = "opsropz-tfstate"
    key            = "infra/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "opsropz-tflocks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

locals {
  common_tags = {
    Project     = "OpsRopz"
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "Terraform"
  }
}
