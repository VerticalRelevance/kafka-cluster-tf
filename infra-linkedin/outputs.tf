output "lambda_function_name" {
  value = aws_lambda_function.finder.function_name
}

output "dynamo_table" {
  value = aws_dynamodb_table.finder.name
}

output "secret_name" {
  description = "Put ANTHROPIC_API_KEY + provider key JSON here."
  value       = aws_secretsmanager_secret.keys.name
}
