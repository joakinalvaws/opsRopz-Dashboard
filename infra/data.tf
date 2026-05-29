# Capa de datos serverless — Semana 1
# Tabla de operaciones (KPIs e historial) + cola de eventos con DLQ.

resource "aws_dynamodb_table" "operations" {
  name         = "${var.name_prefix}-operations-${var.environment}"
  billing_mode = "PAY_PER_REQUEST" # on-demand: encaja en la capa gratuita de 25GB
  hash_key     = "sku"
  range_key    = "event_id" # "{timestamp}#{correlation_id}" — único y ordenado por tiempo

  # Stream que dispara el analyzer (Semana 2) con cada nuevo item KPI.
  stream_enabled   = true
  stream_view_type = "NEW_IMAGE"

  attribute {
    name = "sku"
    type = "S"
  }

  attribute {
    name = "event_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.environment == "prod"
  }
}

resource "aws_sqs_queue" "events_dlq" {
  name                      = "${var.name_prefix}-events-dlq-${var.environment}"
  message_retention_seconds = 1209600 # 14 días para análisis posterior
}

resource "aws_sqs_queue" "events" {
  name                       = "${var.name_prefix}-events-${var.environment}"
  visibility_timeout_seconds = 60

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.events_dlq.arn
    maxReceiveCount     = 3
  })
}
