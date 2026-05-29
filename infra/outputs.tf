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
