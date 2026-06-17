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