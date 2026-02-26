output "id" {
  description = "ID of the Azure AI Search service"
  value       = azurerm_search_service.search.id
}

output "name" {
  description = "Name of the Azure AI Search service"
  value       = azurerm_search_service.search.name
}

output "endpoint" {
  description = "Search service endpoint URL"
  value       = "https://${azurerm_search_service.search.name}.search.windows.net"
}

output "primary_key" {
  description = "Primary admin key"
  value       = azurerm_search_service.search.primary_key
  sensitive   = true
}

output "query_key" {
  description = "Primary query key"
  value       = azurerm_search_service.search.query_keys[0].value
  sensitive   = true
}

output "principal_id" {
  description = "Principal ID of the search service's managed identity"
  value       = azurerm_search_service.search.identity[0].principal_id
}
