variable "aws_region" {
  description = "Región AWS donde se despliegan los recursos"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Entorno de despliegue (dev | prod)"
  type        = string

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "environment debe ser 'dev' o 'prod'."
  }
}

variable "owner" {
  description = "Responsable del proyecto (tag de ownership para Cost Explorer)"
  type        = string
  default     = "joakindev"
}

variable "name_prefix" {
  description = "Prefijo para nombrar recursos, namespacing por entorno"
  type        = string
  default     = "opsropz"
}

variable "bedrock_model_id" {
  description = "Inference profile de Bedrock que invoca el analyzer (Claude Haiku 4.5 requiere profile, no el model ID directo)"
  type        = string
  default     = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
}

variable "bedrock_foundation_model" {
  description = "Foundation model subyacente al inference profile (para permisos IAM)"
  type        = string
  default     = "anthropic.claude-haiku-4-5-20251001-v1:0"
}

variable "bedrock_profile_regions" {
  description = "Regiones que abarca el inference profile us.* (invoke requiere permiso sobre el FM en cada una)"
  type        = list(string)
  default     = ["us-east-1", "us-east-2", "us-west-2"]
}
