# IAM con mínimo privilegio — un rol por Lambda, solo los permisos necesarios.

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# --- Rol de la Lambda processor ---

resource "aws_iam_role" "processor" {
  name               = "${var.name_prefix}-processor-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

data "aws_iam_policy_document" "processor" {
  # Leer y borrar mensajes de la cola de eventos (consumo SQS).
  statement {
    sid = "ConsumeEvents"
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
    ]
    resources = [aws_sqs_queue.events.arn]
  }

  # Escribir items normalizados en la tabla de operaciones.
  statement {
    sid       = "WriteOperations"
    actions   = ["dynamodb:PutItem"]
    resources = [aws_dynamodb_table.operations.arn]
  }
}

resource "aws_iam_role_policy" "processor" {
  name   = "${var.name_prefix}-processor-policy-${var.environment}"
  role   = aws_iam_role.processor.id
  policy = data.aws_iam_policy_document.processor.json
}

# Logs a CloudWatch (política gestionada mínima para Lambda).
resource "aws_iam_role_policy_attachment" "processor_logs" {
  role       = aws_iam_role.processor.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# --- Rol de la Lambda analyzer ---

resource "aws_iam_role" "analyzer" {
  name               = "${var.name_prefix}-analyzer-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

data "aws_iam_policy_document" "analyzer" {
  # Leer el stream de la tabla operations (trigger del analyzer).
  statement {
    sid = "ReadOperationsStream"
    actions = [
      "dynamodb:GetRecords",
      "dynamodb:GetShardIterator",
      "dynamodb:DescribeStream",
      "dynamodb:ListStreams",
    ]
    resources = [aws_dynamodb_table.operations.stream_arn]
  }

  # Invocar Claude Haiku 4.5 vía inference profile us.*: requiere permiso sobre el
  # perfil y sobre el foundation-model en cada región que el perfil abarca.
  statement {
    sid     = "InvokeBedrockModel"
    actions = ["bedrock:InvokeModel"]
    resources = concat(
      [
        "arn:aws:bedrock:${var.aws_region}:${data.aws_caller_identity.current.account_id}:inference-profile/${var.bedrock_model_id}",
      ],
      [
        for r in var.bedrock_profile_regions :
        "arn:aws:bedrock:${r}::foundation-model/${var.bedrock_foundation_model}"
      ],
    )
  }

  # Publicar alertas al topic SNS (Semana 3).
  statement {
    sid       = "PublishAlerts"
    actions   = ["sns:Publish"]
    resources = [aws_sns_topic.ops_alerts.arn]
  }

  # Persistir alertas en la tabla de historial (Semana 4).
  statement {
    sid       = "WriteAlerts"
    actions   = ["dynamodb:PutItem"]
    resources = [aws_dynamodb_table.alerts.arn]
  }
}

resource "aws_iam_role_policy" "analyzer" {
  name   = "${var.name_prefix}-analyzer-policy-${var.environment}"
  role   = aws_iam_role.analyzer.id
  policy = data.aws_iam_policy_document.analyzer.json
}

resource "aws_iam_role_policy_attachment" "analyzer_logs" {
  role       = aws_iam_role.analyzer.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# --- Rol de la Lambda dlq_monitor ---

resource "aws_iam_role" "dlq_monitor" {
  name               = "${var.name_prefix}-dlq-monitor-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

data "aws_iam_policy_document" "dlq_monitor" {
  statement {
    sid       = "ReadDLQAttributes"
    actions   = ["sqs:GetQueueAttributes"]
    resources = [aws_sqs_queue.events_dlq.arn]
  }

  statement {
    sid       = "PublishAlerts"
    actions   = ["sns:Publish"]
    resources = [aws_sns_topic.ops_alerts.arn]
  }
}

resource "aws_iam_role_policy" "dlq_monitor" {
  name   = "${var.name_prefix}-dlq-monitor-policy-${var.environment}"
  role   = aws_iam_role.dlq_monitor.id
  policy = data.aws_iam_policy_document.dlq_monitor.json
}

resource "aws_iam_role_policy_attachment" "dlq_monitor_logs" {
  role       = aws_iam_role.dlq_monitor.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# --- Rol de la Lambda daily_report ---

resource "aws_iam_role" "daily_report" {
  name               = "${var.name_prefix}-daily-report-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

data "aws_iam_policy_document" "daily_report" {
  statement {
    sid       = "ScanOperations"
    actions   = ["dynamodb:Scan"]
    resources = [aws_dynamodb_table.operations.arn]
  }

  # SES SendEmail no admite restricción por identidad de forma consistente en
  # todos los escenarios de sandbox/producción; se usa "*" y se confía en el
  # rol como límite de blast radius.
  statement {
    sid       = "SendEmail"
    actions   = ["ses:SendEmail"]
    resources = ["*"]
  }

  statement {
    sid       = "PublishReport"
    actions   = ["sns:Publish"]
    resources = [aws_sns_topic.ops_alerts.arn]
  }
}

resource "aws_iam_role_policy" "daily_report" {
  name   = "${var.name_prefix}-daily-report-policy-${var.environment}"
  role   = aws_iam_role.daily_report.id
  policy = data.aws_iam_policy_document.daily_report.json
}

resource "aws_iam_role_policy_attachment" "daily_report_logs" {
  role       = aws_iam_role.daily_report.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# --- Rol de la Lambda query (Semana 4) ---

resource "aws_iam_role" "query" {
  name               = "${var.name_prefix}-query-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

data "aws_iam_policy_document" "query" {
  # Solo lectura: scan de operations + query de alerts.
  statement {
    sid = "ReadData"
    actions = [
      "dynamodb:Scan",
      "dynamodb:Query",
      "dynamodb:GetItem",
    ]
    resources = [
      aws_dynamodb_table.operations.arn,
      aws_dynamodb_table.alerts.arn,
    ]
  }
}

resource "aws_iam_role_policy" "query" {
  name   = "${var.name_prefix}-query-policy-${var.environment}"
  role   = aws_iam_role.query.id
  policy = data.aws_iam_policy_document.query.json
}

resource "aws_iam_role_policy_attachment" "query_logs" {
  role       = aws_iam_role.query.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
