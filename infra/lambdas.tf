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
    }
  }
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
