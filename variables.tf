variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-2"
}

variable "project_name" {
  description = "Name prefix for all resources"
  type        = string
  default     = "kafka-cluster"
}

variable "instance_type" {
  description = "EC2 instance type for the Kafka broker"
  type        = string
  default     = "t3.medium"
}

variable "key_pair_name" {
  description = "Name of an existing EC2 key pair for SSH access"
  type        = string
}

variable "codestar_connection_arn" {
  description = "ARN of the CodeStar connection to GitHub"
  type        = string
   default     = "arn:aws:codeconnections:us-east-2:899456967600:connection/4bf85604-5fdc-47cb-b2c9-5ba0627899d3"
}