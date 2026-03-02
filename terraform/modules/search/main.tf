# Azure AI Search Module
# Provides search service with semantic ranking for RAG pattern

resource "azurerm_search_service" "search" {
  name                = var.name
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = var.sku

  semantic_search_sku          = var.semantic_search_sku
  authentication_failure_mode  = "http401WithBearerChallenge"

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}
