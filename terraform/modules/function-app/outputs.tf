output "function_app_id" {
  description = "ID of the Function App"
  value       = azurerm_linux_function_app.processor.id
}

output "function_app_name" {
  description = "Name of the Function App"
  value       = azurerm_linux_function_app.processor.name
}

output "function_app_default_hostname" {
  description = "Default hostname of the Function App"
  value       = azurerm_linux_function_app.processor.default_hostname
}

output "function_app_principal_id" {
  description = "Principal ID of the Function App's managed identity"
  value       = azurerm_linux_function_app.processor.identity[0].principal_id
}

output "application_insights_instrumentation_key" {
  description = "Application Insights instrumentation key"
  value       = azurerm_application_insights.function_insights.instrumentation_key
  sensitive   = true
}

output "application_insights_connection_string" {
  description = "Application Insights connection string"
  value       = azurerm_application_insights.function_insights.connection_string
  sensitive   = true
}
