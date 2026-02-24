output "id" {
  description = "ID of the Document Intelligence service"
  value       = azurerm_cognitive_account.doc_intelligence.id
}

output "name" {
  description = "Name of the Document Intelligence service"
  value       = azurerm_cognitive_account.doc_intelligence.name
}

output "endpoint" {
  description = "Endpoint URL"
  value       = azurerm_cognitive_account.doc_intelligence.endpoint
}

output "primary_access_key" {
  description = "Primary access key"
  value       = azurerm_cognitive_account.doc_intelligence.primary_access_key
  sensitive   = true
}
