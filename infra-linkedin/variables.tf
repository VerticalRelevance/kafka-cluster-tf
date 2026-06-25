variable "region" {
  type    = string
  default = "us-east-1"
}

variable "name_prefix" {
  type    = string
  default = "linkedin-finder"
}

variable "people_source" {
  description = "Licensed data provider connector: pdl | apollo (stub for testing)"
  type        = string
  default     = "pdl"
}

variable "daily_target" {
  type    = string
  default = "50"
}

variable "schedule_expression" {
  description = "EventBridge Scheduler cron. Default: 13:00 UTC daily."
  type        = string
  default     = "cron(0 13 * * ? *)"
}
