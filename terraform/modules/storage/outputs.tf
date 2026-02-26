output "storage_account_id" {
  description = "ID of the storage account"
  value       = azurerm_storage_account.storage.id
}

output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.storage.name
}

output "primary_access_key" {
  description = "Primary access key"
  value       = azurerm_storage_account.storage.primary_access_key
  sensitive   = true
}

output "primary_connection_string" {
  description = "Primary connection string"
  value       = azurerm_storage_account.storage.primary_connection_string
  sensitive   = true
}

output "claims_container_name" {
  description = "Name of the claims container"
  value       = azurerm_storage_container.claims.name
}

output "processed_container_name" {
  description = "Name of the processed data container"
  value       = azurerm_storage_container.processed.name
}

output "terms_container_name" {
  description = "Name of the terms and conditions container"
  value       = azurerm_storage_container.terms_and_conditions.name
}
