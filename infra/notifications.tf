# Semana 3 — Notificaciones: SNS + EventBridge

# Topic central de alertas operacionales. Todos los componentes (analyzer,
# dlq_monitor, daily_report) publican aquí; n8n se suscribe para enrutar
# las alertas a Slack y WhatsApp según severidad.
resource "aws_sns_topic" "ops_alerts" {
  name = "${var.name_prefix}-ops-alerts-${var.environment}"
}

# Suscripción del webhook n8n. Solo se crea si se provee la URL en tfvars.
# SNS confirma la suscripción automáticamente visitando la URL de confirmación.
resource "aws_sns_topic_subscription" "n8n_webhook" {
  count     = var.n8n_webhook_url != "" ? 1 : 0
  topic_arn = aws_sns_topic.ops_alerts.arn
  protocol  = "https"
  endpoint  = var.n8n_webhook_url

  endpoint_auto_confirms = true
}

# --- EventBridge: reporte diario a las 8am UTC ---

resource "aws_cloudwatch_event_rule" "daily_report" {
  name                = "${var.name_prefix}-daily-report-${var.environment}"
  description         = "Dispara la Lambda de reporte diario a las 8am UTC"
  schedule_expression = "cron(0 8 * * ? *)"
}

resource "aws_cloudwatch_event_target" "daily_report" {
  rule      = aws_cloudwatch_event_rule.daily_report.name
  target_id = "daily_report_lambda"
  arn       = aws_lambda_function.daily_report.arn
}

resource "aws_lambda_permission" "daily_report_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.daily_report.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_report.arn
}

# --- EventBridge: monitoreo de DLQ cada 6 horas ---

resource "aws_cloudwatch_event_rule" "dlq_check" {
  name                = "${var.name_prefix}-dlq-check-${var.environment}"
  description         = "Verifica la DLQ en busca de mensajes fallidos cada 6 horas"
  schedule_expression = "rate(6 hours)"
}

resource "aws_cloudwatch_event_target" "dlq_check" {
  rule      = aws_cloudwatch_event_rule.dlq_check.name
  target_id = "dlq_monitor_lambda"
  arn       = aws_lambda_function.dlq_monitor.arn
}

resource "aws_lambda_permission" "dlq_monitor_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dlq_monitor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.dlq_check.arn
}
