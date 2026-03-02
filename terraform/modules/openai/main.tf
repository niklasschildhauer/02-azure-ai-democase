# Azure OpenAI Module
# Provides chat completion and embedding models

resource "azurerm_cognitive_account" "openai" {
  name                  = var.name
  resource_group_name   = var.resource_group_name
  location              = var.location
  kind                  = "OpenAI"
  sku_name              = var.sku_name
  custom_subdomain_name = var.name

  tags = var.tags
}

# Deploy chat completion model
resource "azurerm_cognitive_deployment" "gpt4" {
  count                = var.deploy_gpt4 ? 1 : 0
  name                 = var.gpt4_deployment_name
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = var.gpt4_model_name
    version = var.gpt4_model_version
  }

  sku {
    name     = "DataZoneStandard"
    capacity = var.gpt4_capacity
  }
}

# Deploy text-embedding model
resource "azurerm_cognitive_deployment" "embedding" {
  count                = var.deploy_embedding ? 1 : 0
  name                 = var.embedding_deployment_name
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = var.embedding_model_name
    version = var.embedding_model_version
  }

  sku {
    name     = "DataZoneStandard"
    capacity = var.embedding_capacity
  }
}
