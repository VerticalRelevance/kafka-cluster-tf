# Minimal serverless stack for the LinkedIn connection finder (Phase 0).
# Separate from the Kafka stack on purpose. Human-in-the-loop: this runs
# discovery + ranking + drafting daily; sending stays manual.

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

provider "aws" {
  region = var.region
}

# --- State table: seen-people + daily batches -------------------------------
resource "aws_dynamodb_table" "finder" {
  name         = "${var.name_prefix}-store"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }
  attribute {
    name = "sk"
    type = "S"
  }
}

# --- Secrets: provider + Anthropic keys -------------------------------------
resource "aws_secretsmanager_secret" "keys" {
  name = "${var.name_prefix}-keys"
}

# --- Lambda packaging --------------------------------------------------------
data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../app"
  output_path = "${path.module}/build/finder.zip"
  excludes    = ["**/__pycache__/**", "**/.data/**", "**/*.pyc"]
}

resource "aws_iam_role" "lambda" {
  name = "${var.name_prefix}-lambda"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "lambda" {
  name = "${var.name_prefix}-lambda-policy"
  role = aws_iam_role.lambda.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:Query", "dynamodb:PutItem", "dynamodb:BatchWriteItem", "dynamodb:GetItem"]
        Resource = aws_dynamodb_table.finder.arn
      },
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = aws_secretsmanager_secret.keys.arn
      }
    ]
  })
}

resource "aws_lambda_function" "finder" {
  function_name    = "${var.name_prefix}-daily"
  role             = aws_iam_role.lambda.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  timeout          = 300
  memory_size      = 512

  environment {
    variables = {
      STORE_BACKEND = "dynamo"
      DYNAMO_TABLE  = aws_dynamodb_table.finder.name
      PEOPLE_SOURCE = var.people_source
      DAILY_TARGET  = tostring(var.daily_target)
      # Inject ANTHROPIC_API_KEY / provider keys from Secrets Manager at deploy
      # time or fetch them inside the handler. Left out here to avoid plaintext.
    }
  }
}

# --- Daily schedule ----------------------------------------------------------
resource "aws_scheduler_schedule" "daily" {
  name = "${var.name_prefix}-daily"
  flexible_time_window {
    mode = "OFF"
  }
  schedule_expression = var.schedule_expression # default 13:00 UTC daily
  target {
    arn      = aws_lambda_function.finder.arn
    role_arn = aws_iam_role.scheduler.arn
  }
}

resource "aws_iam_role" "scheduler" {
  name = "${var.name_prefix}-scheduler"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "scheduler.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "scheduler" {
  name = "${var.name_prefix}-scheduler-policy"
  role = aws_iam_role.scheduler.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["lambda:InvokeFunction"]
      Resource = aws_lambda_function.finder.arn
    }]
  })
}
