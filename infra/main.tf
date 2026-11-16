
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_cloudwatch_log_group" "greenwheels" {
  name              = "/greenwheels/fleet-lease-service"
  retention_in_days = 30

  tags = {
    Project     = "Greenwheels"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Count application ERROR log entries.
resource "aws_cloudwatch_log_metric_filter" "application_errors" {
  name           = "GreenwheelsApplicationErrors"
  log_group_name = aws_cloudwatch_log_group.greenwheels.name
  pattern        = "{ $.level = \"ERROR\" }"

  metric_transformation {
    name      = "ApplicationErrorCount"
    namespace = "Greenwheels/SRE"
    value     = "1"
  }
}

# Extract request latency from structured JSON logs.
resource "aws_cloudwatch_log_metric_filter" "request_latency" {
  name           = "GreenwheelsRequestLatency"
  log_group_name = aws_cloudwatch_log_group.greenwheels.name
  pattern        = "{ $.latency_ms = * }"

  metric_transformation {
    name      = "RequestLatency"
    namespace = "Greenwheels/SRE"
    value     = "$.latency_ms"
    unit      = "Milliseconds"
  }
}

# Alert when application errors exceed five in a five-minute period.
resource "aws_cloudwatch_metric_alarm" "high_error_count" {
  alarm_name          = "Greenwheels-High-Application-Errors"
  alarm_description   = "Application error count exceeded the configured threshold."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = aws_cloudwatch_log_metric_filter.application_errors.metric_transformation[0].name
  namespace           = "Greenwheels/SRE"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  treat_missing_data  = "notBreaching"
}

# Alert when average request latency exceeds 300 milliseconds.
resource "aws_cloudwatch_metric_alarm" "high_request_latency" {
  alarm_name          = "Greenwheels-High-Request-Latency"
  alarm_description   = "Average request latency exceeded 300 milliseconds."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = aws_cloudwatch_log_metric_filter.request_latency.metric_transformation[0].name
  namespace           = "Greenwheels/SRE"
  period              = 300
  statistic           = "Average"
  threshold           = 300
  treat_missing_data  = "notBreaching"
}
