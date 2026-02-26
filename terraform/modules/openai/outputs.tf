output "id" {
  description = "ID of the Azure OpenAI service"
  value       = azurerm_cognitive_account.openai.id
}

output "name" {
  description = "Name of the Azure OpenAI service"
  value       = azurerm_cognitive_account.openai.name
}

output "endpoint" {
  description = "OpenAI service endpoint"
  value       = azurerm_cognitive_account.openai.endpoint
}

output "primary_access_key" {
  description = "Primary access key"
  value       = azurerm_cognitive_account.openai.primary_access_key
  sensitive   = true
}

output "gpt4_deployment_name" {
  description = "Name of the chat model deployment"
  value       = var.deploy_gpt4 ? azurerm_cognitive_deployment.gpt4[0].name : null
}

output "embedding_deployment_name" {
  description = "Name of the embedding deployment"
  value       = var.deploy_embedding ? azurerm_cognitive_deployment.embedding[0].name : null
}
