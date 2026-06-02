# Funciones Lambda. El empaquetado lo hace Terraform con archive_file para que
# `terraform apply` sea autosuficiente en desarrollo (en CI se reemplaza por un
# artefacto construido en el pipeline de deploy).

data "archive_file" "processor" {
  type        = "zip"
  source_dir  = "${path.module}/../lambdas/processor"
  output_path = "${path.module}/.build/processor.zip"
  excludes    = ["tests", "README.md", "requirements.txt", "__pycache__"]
}

resource "aws_lambda_function" "processor" {
  function_name    = "${var.name_prefix}-processor-${var.environment}"
  role             = aws_iam_role.processor.arn
  runtime          = "python3.12"
  handler          = "handler.lambda_handler"
  filename         = data.archive_file.processor.output_path
  source_code_hash = data.archive_file.processor.output_base64sha256
  timeout          = 30
  memory_size      = 128

  environment {
    variables = {
      OPERATIONS_TABLE = aws_dynamodb_table.operations.name
    }
  }
}

resource "aws_lambda_event_source_mapping" "processor_sqs" {
  event_source_arn                   = aws_sqs_queue.events.arn
  function_name                      = aws_lambda_function.processor.arn
  batch_size                         = 10
  maximum_batching_window_in_seconds = 5

  # Habilita el reporte de fallos parciales que devuelve el handler.
  function_response_types = ["ReportBatchItemFailures"]
}

resource "aws_cloudwatch_log_group" "processor" {
  name              = "/aws/lambda/${aws_lambda_function.processor.function_name}"
  retention_in_days = 14
}

# --- analyzer (Semana 2): detección de anomalías + Bedrock ---

data "archive_file" "analyzer" {
  type        = "zip"
  source_dir  = "${path.module}/../lambdas/analyzer"
  output_path = "${path.module}/.build/analyzer.zip"
  excludes    = ["tests", "README.md", "requirements.txt", "__pycache__"]
}

resource "aws_lambda_function" "analyzer" {
  function_name    = "${var.name_prefix}-analyzer-${var.environment}"
  role             = aws_iam_role.analyzer.arn
  runtime          = "python3.12"
  handler          = "handler.lambda_handler"
  filename         = data.archive_file.analyzer.output_path
  source_code_hash = data.archive_file.analyzer.output_base64sha256
  timeout          = 30
  memory_size      = 256

  environment {
    variables = {
      BEDROCK_MODEL_ID = var.bedrock_model_id
      SNS_TOPIC_ARN    = aws_sns_topic.ops_alerts.arn
    }
  }
}

# --- dlq_monitor (Semana 3): revisa la DLQ cada 6h y alerta si hay mensajes ---

data "archive_file" "dlq_monitor" {
  type        = "zip"
  source_dir  = "${path.module}/../lambdas/dlq_monitor"
  output_path = "${path.module}/.build/dlq_monitor.zip"
  excludes    = ["tests", "README.md", "requirements.txt", "__pycache__"]
}

resource "aws_lambda_function" "dlq_monitor" {
  function_name    = "${var.name_prefix}-dlq-monitor-${var.environment}"
  role             = aws_iam_role.dlq_monitor.arn
  runtime          = "python3.12"
  handler          = "handler.lambda_handler"
  filename         = data.archive_file.dlq_monitor.output_path
  source_code_hash = data.archive_file.dlq_monitor.output_base64sha256
  timeout          = 30
  memory_size      = 128

  environment {
    variables = {
      DLQ_URL       = aws_sqs_queue.events_dlq.url
      SNS_TOPIC_ARN = aws_sns_topic.ops_alerts.arn
    }
  }
}

resource "aws_cloudwatch_log_group" "dlq_monitor" {
  name              = "/aws/lambda/${aws_lambda_function.dlq_monitor.function_name}"
  retention_in_days = 14
}

# --- daily_report (Semana 3): resumen diario a las 8am vía SES ---

data "archive_file" "daily_report" {
  type        = "zip"
  source_dir  = "${path.module}/../lambdas/daily_report"
  output_path = "${path.module}/.build/daily_report.zip"
  excludes    = ["tests", "README.md", "requirements.txt", "__pycache__"]
}

resource "aws_lambda_function" "daily_report" {
  function_name    = "${var.name_prefix}-daily-report-${var.environment}"
  role             = aws_iam_role.daily_report.arn
  runtime          = "python3.12"
  handler          = "handler.lambda_handler"
  filename         = data.archive_file.daily_report.output_path
  source_code_hash = data.archive_file.daily_report.output_base64sha256
  timeout          = 60
  memory_size      = 128

  environment {
    variables = {
      OPERATIONS_TABLE = aws_dynamodb_table.operations.name
      SNS_TOPIC_ARN    = aws_sns_topic.ops_alerts.arn
      SES_SENDER       = var.ses_sender
      SES_RECIPIENT    = var.ses_recipient
    }
  }
}

resource "aws_cloudwatch_log_group" "daily_report" {
  name              = "/aws/lambda/${aws_lambda_function.daily_report.function_name}"
  retention_in_days = 14
}

resource "aws_lambda_event_source_mapping" "analyzer_stream" {
  event_source_arn                   = aws_dynamodb_table.operations.stream_arn
  function_name                      = aws_lambda_function.analyzer.arn
  starting_position                  = "LATEST"
  batch_size                         = 10
  maximum_batching_window_in_seconds = 5
  function_response_types            = ["ReportBatchItemFailures"]
}

resource "aws_cloudwatch_log_group" "analyzer" {
  name              = "/aws/lambda/${aws_lambda_function.analyzer.function_name}"
  retention_in_days = 14
}
