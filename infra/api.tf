# Semana 4 — API Gateway REST que expone la Lambda query al dashboard.
# Protegido con API key + usage plan (rate limiting). La key vive server-side en
# el backend de Next.js (Vercel), nunca en el navegador.

resource "aws_api_gateway_rest_api" "dashboard" {
  name        = "${var.name_prefix}-dashboard-${var.environment}"
  description = "API de KPIs y alertas para el dashboard OpsRopz"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

# Recursos /kpis y /alerts
resource "aws_api_gateway_resource" "kpis" {
  rest_api_id = aws_api_gateway_rest_api.dashboard.id
  parent_id   = aws_api_gateway_rest_api.dashboard.root_resource_id
  path_part   = "kpis"
}

resource "aws_api_gateway_resource" "alerts" {
  rest_api_id = aws_api_gateway_rest_api.dashboard.id
  parent_id   = aws_api_gateway_rest_api.dashboard.root_resource_id
  path_part   = "alerts"
}

# Métodos GET con API key obligatoria
resource "aws_api_gateway_method" "kpis_get" {
  rest_api_id      = aws_api_gateway_rest_api.dashboard.id
  resource_id      = aws_api_gateway_resource.kpis.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_method" "alerts_get" {
  rest_api_id      = aws_api_gateway_rest_api.dashboard.id
  resource_id      = aws_api_gateway_resource.alerts.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true
}

# Integraciones Lambda proxy
resource "aws_api_gateway_integration" "kpis" {
  rest_api_id             = aws_api_gateway_rest_api.dashboard.id
  resource_id             = aws_api_gateway_resource.kpis.id
  http_method             = aws_api_gateway_method.kpis_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.query.invoke_arn
}

resource "aws_api_gateway_integration" "alerts" {
  rest_api_id             = aws_api_gateway_rest_api.dashboard.id
  resource_id             = aws_api_gateway_resource.alerts.id
  http_method             = aws_api_gateway_method.alerts_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.query.invoke_arn
}

# Permiso para que API Gateway invoque la Lambda query
resource "aws_lambda_permission" "api_query" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.query.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.dashboard.execution_arn}/*/*"
}

# Deployment + stage. El trigger fuerza re-deploy cuando cambian métodos/integraciones.
resource "aws_api_gateway_deployment" "dashboard" {
  rest_api_id = aws_api_gateway_rest_api.dashboard.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.kpis.id,
      aws_api_gateway_resource.alerts.id,
      aws_api_gateway_method.kpis_get.id,
      aws_api_gateway_method.alerts_get.id,
      aws_api_gateway_integration.kpis.id,
      aws_api_gateway_integration.alerts.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "dashboard" {
  deployment_id = aws_api_gateway_deployment.dashboard.id
  rest_api_id   = aws_api_gateway_rest_api.dashboard.id
  stage_name    = var.environment
}

# --- API key + usage plan (rate limiting) ---

resource "aws_api_gateway_api_key" "dashboard" {
  name = "${var.name_prefix}-dashboard-key-${var.environment}"
}

resource "aws_api_gateway_usage_plan" "dashboard" {
  name = "${var.name_prefix}-dashboard-plan-${var.environment}"

  api_stages {
    api_id = aws_api_gateway_rest_api.dashboard.id
    stage  = aws_api_gateway_stage.dashboard.stage_name
  }

  # Rate limiting: 100 req/min sostenido (~1.67/s), ráfaga de 20.
  throttle_settings {
    rate_limit  = 1.67
    burst_limit = 20
  }

  # Cuota mensual generosa pero acotada (capa gratuita).
  quota_settings {
    limit  = 100000
    period = "MONTH"
  }
}

resource "aws_api_gateway_usage_plan_key" "dashboard" {
  key_id        = aws_api_gateway_api_key.dashboard.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.dashboard.id
}
