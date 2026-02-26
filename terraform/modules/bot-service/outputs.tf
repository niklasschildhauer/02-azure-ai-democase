output "id" {
  description = "ID of the Bot Service"
  value       = azurerm_bot_service_azure_bot.bot.id
}

output "name" {
  description = "Name of the Bot Service"
  value       = azurerm_bot_service_azure_bot.bot.name
}
