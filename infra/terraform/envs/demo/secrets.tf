# OpenRouter API key shell only — set SecretString once in the AWS console (never in Terraform state).
resource "aws_secretsmanager_secret" "openrouter_api_key" {
  name        = "complibot-demo/openrouter-api-key"
  description = "OpenRouter API key for the CompliBot demo worker (value set manually in the console)."
}
