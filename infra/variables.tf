
variable "aws_region" {
  description = "AWS region for Greenwheels monitoring resources."
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "dev"
}
