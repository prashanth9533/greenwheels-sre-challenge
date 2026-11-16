
output "cloudwatch_log_group_name" {
  description = "CloudWatch log group for the Greenwheels service."
  value       = aws_cloudwatch_log_group.greenwheels.name
}

output "error_alarm_name" {
  description = "CloudWatch application error alarm."
  value       = aws_cloudwatch_metric_alarm.high_error_count.alarm_name
}

output "latency_alarm_name" {
  description = "CloudWatch request latency alarm."
  value       = aws_cloudwatch_metric_alarm.high_request_latency.alarm_name
}
