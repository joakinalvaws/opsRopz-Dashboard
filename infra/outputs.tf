output "operations_table_name" {
  description = "Nombre de la tabla DynamoDB de operaciones"
  value       = aws_dynamodb_table.operations.name
}

output "events_queue_url" {
  description = "URL de la cola SQS de eventos (destino del simulador)"
  value       = aws_sqs_queue.events.url
}

output "events_queue_arn" {
  description = "ARN de la cola SQS de eventos (trigger de la Lambda processor)"
  value       = aws_sqs_queue.events.arn
}

output "events_dlq_url" {
  description = "URL de la Dead Letter Queue"
  value       = aws_sqs_queue.events_dlq.url
}

output "processor_function_name" {
  description = "Nombre de la Lambda processor"
  value       = aws_lambda_function.processor.function_name
}

output "analyzer_function_name" {
  description = "Nombre de la Lambda analyzer"
  value       = aws_lambda_function.analyzer.function_name
}

output "ops_alerts_topic_arn" {
  description = "ARN del topic SNS de alertas operacionales"
  value       = aws_sns_topic.ops_alerts.arn
}

output "dlq_monitor_function_name" {
  description = "Nombre de la Lambda dlq_monitor"
  value       = aws_lambda_function.dlq_monitor.function_name
}

output "daily_report_function_name" {
  description = "Nombre de la Lambda daily_report"
  value       = aws_lambda_function.daily_report.function_name
}

output "cloudwatch_dashboard_url" {
  description = "URL del CloudWatch Dashboard en la consola de AWS"
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}

output "alerts_table_name" {
  description = "Nombre de la tabla DynamoDB de alertas (historial)"
  value       = aws_dynamodb_table.alerts.name
}

output "query_function_name" {
  description = "Nombre de la Lambda query"
  value       = aws_lambda_function.query.function_name
}

output "dashboard_api_url" {
  description = "URL base del API Gateway del dashboard (endpoints /kpis y /alerts)"
  value       = aws_api_gateway_stage.dashboard.invoke_url
}

output "dashboard_api_key" {
  description = "API key para el dashboard (usar server-side en Vercel, no en el navegador)"
  value       = aws_api_gateway_api_key.dashboard.value
  sensitive   = true
}
