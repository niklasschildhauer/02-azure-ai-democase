output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.rg.name
}

output "resource_group_id" {
  description = "ID of the resource group"
  value       = azurerm_resource_group.rg.id
}

# Storage Outputs
output "storage_account_name" {
  description = "Name of the storage account for claims"
  value       = module.storage.storage_account_name
}

output "storage_account_key" {
  description = "Primary access key for storage account"
  value       = module.storage.primary_access_key
  sensitive   = true
}

output "claims_container_name" {
  description = "Name of the blob container for insurance claims"
  value       = module.storage.claims_container_name
}

output "processed_container_name" {
  description = "Name of the blob container for processed data"
  value       = module.storage.processed_container_name
}

output "storage_connection_string" {
  description = "Connection string for storage account"
  value       = module.storage.primary_connection_string
  sensitive   = true
}

# Document Intelligence Outputs
output "doc_intelligence_name" {
  description = "Name of Azure AI Document Intelligence"
  value       = module.document_intelligence.name
}

output "doc_intelligence_endpoint" {
  description = "Endpoint for Azure AI Document Intelligence"
  value       = module.document_intelligence.endpoint
}

output "doc_intelligence_key" {
  description = "Primary key for Azure AI Document Intelligence"
  value       = module.document_intelligence.primary_access_key
  sensitive   = true
}

# OpenAI Outputs
output "openai_endpoint" {
  description = "Endpoint for Azure OpenAI service"
  value       = module.openai.endpoint
}

output "openai_name" {
  description = "Name of the Azure OpenAI service"
  value       = module.openai.name
}

# Search Outputs
output "search_endpoint" {
  description = "Endpoint for Azure AI Search service"
  value       = module.search.endpoint
}

output "search_name" {
  description = "Name of the Azure AI Search service"
  value       = module.search.name
}

output "search_admin_key" {
  description = "Admin key for Azure AI Search"
  value       = module.search.primary_key
  sensitive   = true
}

# Bot Service Outputs
output "bot_name" {
  description = "Name of the Bot Service"
  value       = module.bot_service.name
}

# Terms and Conditions Container
output "terms_container_name" {
  description = "Name of the terms and conditions blob container"
  value       = module.storage.terms_container_name
}

# Document Intelligence ID (for search setup script)
output "doc_intelligence_id" {
  description = "Resource ID of Document Intelligence service"
  value       = module.document_intelligence.id
}

# AI Services Outputs
output "ai_services_endpoint" {
  description = "Endpoint for Azure AI Services (multi-service)"
  value       = module.ai_services.endpoint
}

# Summary output for easy reference
output "deployment_summary" {
  description = "Summary of deployed resources"
  value = {
    resource_group   = azurerm_resource_group.rg.name
    location         = azurerm_resource_group.rg.location
    storage_account  = module.storage.storage_account_name
    claims_container = module.storage.claims_container_name
    terms_container  = module.storage.terms_container_name
    doc_intelligence = module.document_intelligence.name
    openai           = module.openai.name
    search           = module.search.name
    bot_service      = module.bot_service.name
  }
}
