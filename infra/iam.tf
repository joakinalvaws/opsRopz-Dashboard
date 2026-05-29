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
