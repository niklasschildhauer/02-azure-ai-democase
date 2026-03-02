output "id" {
  description = "ID of the AI Services resource"
  value       = azurerm_cognitive_account.ai_services.id
}

output "name" {
  description = "Name of the AI Services resource"
  value       = azurerm_cognitive_account.ai_services.name
}

output "endpoint" {
  description = "AI Services endpoint"
  value       = azurerm_cognitive_account.ai_services.endpoint
}
