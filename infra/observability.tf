# Semana 3 — Observabilidad: CloudWatch Dashboard + Alarms

locals {
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "Lambda — Invocaciones"
          view    = "timeSeries"
          region  = var.aws_region
          period  = 300
          stacked = false
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.processor.function_name, { label = "processor" }],
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.analyzer.function_name, { label = "analyzer" }],
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.dlq_monitor.function_name, { label = "dlq_monitor" }],
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.daily_report.function_name, { label = "daily_report" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "Lambda — Errores"
          view    = "timeSeries"
          region  = var.aws_region
          period  = 300
          stacked = false
          metrics = [
            ["AWS/Lambda", "Errors", "FunctionName", aws_lambda_function.processor.function_name, { label = "processor", color = "#d62728" }],
            ["AWS/Lambda", "Errors", "FunctionName", aws_lambda_function.analyzer.function_name, { label = "analyzer", color = "#ff7f0e" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title   = "Lambda — Duración p95 (ms)"
          view    = "timeSeries"
          region  = var.aws_region
          period  = 300
          stacked = false
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", aws_lambda_function.processor.function_name, { stat = "p95", label = "processor p95" }],
            ["AWS/Lambda", "Duration", "FunctionName", aws_lambda_function.analyzer.function_name, { stat = "p95", label = "analyzer p95" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 6
        height = 6
        properties = {
          title   = "DLQ — Mensajes pendientes"
          view    = "timeSeries"
          region  = var.aws_region
          period  = 300
          stacked = false
          metrics = [
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", aws_sqs_queue.events_dlq.name, { color = "#d62728" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 18
        y      = 6
        width  = 6
        height = 6
        properties = {
          title   = "SNS — Alertas publicadas"
          view    = "timeSeries"
          region  = var.aws_region
          period  = 300
          stacked = false
          metrics = [
            ["AWS/SNS", "NumberOfMessagesPublished", "TopicName", aws_sns_topic.ops_alerts.name],
          ]
        }
      },
    ]
  })
}

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.name_prefix}-${var.environment}"
  dashboard_body = local.dashboard_body
}

# --- Alarmas ---

# Más de 2 errores en el processor en una ventana de 5 minutos.
resource "aws_cloudwatch_metric_alarm" "processor_errors" {
  alarm_name          = "${var.name_prefix}-processor-errors-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  threshold           = 2
  alarm_description   = "Lambda processor: más de 2 errores en 5 minutos"
  alarm_actions       = [aws_sns_topic.ops_alerts.arn]
  ok_actions          = [aws_sns_topic.ops_alerts.arn]
  treat_missing_data  = "notBreaching"

  metric_name = "Errors"
  namespace   = "AWS/Lambda"
  period      = 300
  statistic   = "Sum"

  dimensions = {
    FunctionName = aws_lambda_function.processor.function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "analyzer_errors" {
  alarm_name          = "${var.name_prefix}-analyzer-errors-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  threshold           = 2
  alarm_description   = "Lambda analyzer: más de 2 errores en 5 minutos"
  alarm_actions       = [aws_sns_topic.ops_alerts.arn]
  ok_actions          = [aws_sns_topic.ops_alerts.arn]
  treat_missing_data  = "notBreaching"

  metric_name = "Errors"
  namespace   = "AWS/Lambda"
  period      = 300
  statistic   = "Sum"

  dimensions = {
    FunctionName = aws_lambda_function.analyzer.function_name
  }
}

# Cualquier mensaje en la DLQ indica un evento perdido — umbral 0.
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  alarm_name          = "${var.name_prefix}-dlq-messages-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  threshold           = 0
  alarm_description   = "DLQ tiene mensajes: eventos fallidos después de 3 reintentos"
  alarm_actions       = [aws_sns_topic.ops_alerts.arn]
  ok_actions          = [aws_sns_topic.ops_alerts.arn]
  treat_missing_data  = "notBreaching"

  metric_name = "ApproximateNumberOfMessagesVisible"
  namespace   = "AWS/SQS"
  period      = 300
  statistic   = "Maximum"

  dimensions = {
    QueueName = aws_sqs_queue.events_dlq.name
  }
}

# Latencia p95 del processor supera 3 segundos en dos períodos consecutivos.
resource "aws_cloudwatch_metric_alarm" "processor_latency" {
  alarm_name          = "${var.name_prefix}-processor-latency-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  threshold           = 3000
  alarm_description   = "Lambda processor: latencia p95 > 3s (posible cuello de botella en DynamoDB)"
  alarm_actions       = [aws_sns_topic.ops_alerts.arn]
  ok_actions          = [aws_sns_topic.ops_alerts.arn]
  treat_missing_data  = "notBreaching"

  metric_name        = "Duration"
  namespace          = "AWS/Lambda"
  period             = 300
  extended_statistic = "p95"

  dimensions = {
    FunctionName = aws_lambda_function.processor.function_name
  }
}
