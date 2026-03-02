terraform {
  required_version = "~> 1.14.4"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.14"
    }
  }

  backend "azurerm" {
    use_azuread_auth = true
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }

    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = true
    }
  }
}

# Data source for current Azure configuration
data "azurerm_client_config" "current" {}

# Used as SQL AAD admin to allow GitHub Actions to create database users
data "azurerm_user_assigned_identity" "github_actions" {
  name                = "id-ccworkshop-github"
  resource_group_name = var.nonprod_acr_resource_group # Same RG as bootstrap resources
}

# # Resource Group
resource "azurerm_resource_group" "rg" {
  name     = "${var.unique_variable_name_suffix}-rg-${var.project_name}"
  location = var.location

  tags = var.tags
}

# Storage Module
module "storage" {
  source = "./modules/storage"

  storage_account_name = "${var.unique_variable_name_suffix}${var.project_name}"
  resource_group_name  = azurerm_resource_group.rg.name
  location             = var.location

  tags = var.tags
}

# Document Intelligence Module
module "document_intelligence" {
  source = "./modules/document-intelligence"

  name                = "${var.unique_variable_name_suffix}-doc-intel-${var.project_name}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = var.location

  tags = var.tags
}

# Function App Module (Blob Trigger for Document Processing)
module "function_app" {
  source = "./modules/function-app"

  function_app_name     = "${var.unique_variable_name_suffix}-func-${var.project_name}"
  service_plan_name     = "${var.unique_variable_name_suffix}-plan-${var.project_name}"
  function_storage_name = "${var.unique_variable_name_suffix}stfunc${var.project_name}"
  app_insights_name     = "${var.unique_variable_name_suffix}-appi-${var.project_name}"

  resource_group_name = azurerm_resource_group.rg.name
  location            = var.location

  # Data storage configuration
  data_storage_connection_string = module.storage.primary_connection_string
  data_storage_account_id        = module.storage.storage_account_id

  # Document Intelligence configuration
  doc_intelligence_endpoint = module.document_intelligence.endpoint
  doc_intelligence_key      = module.document_intelligence.primary_access_key
  doc_intelligence_id       = module.document_intelligence.id

  # Azure OpenAI configuration
  azure_openai_endpoint        = module.ai_services.endpoint
  azure_openai_api_key         = module.ai_services.primary_access_key
  azure_openai_deployment_name = module.ai_services.gpt4_deployment_name
  azure_openai_id              = module.ai_services.ai_services_id
  azure_openai_api_version     = "2025-01-01-preview"

  # Container names
  input_container_name          = module.storage.claims_container_name
  output_container_name         = module.storage.processed_container_name
  model_analysis_container_name = module.storage.model_analysis_container_name

  tags = var.tags

  depends_on = [
    module.storage,
    module.document_intelligence,
    module.ai_services
  ]
}

# Azure AI Services Module (simplified - no hub overhead)
# Just AI Services with GPT-4 and embeddings for Function App to use
module "ai_services" {
  source = "./modules/ai-services"

  resource_group_name = azurerm_resource_group.rg.name
  location            = var.openai_location

  # AI Services account
  ai_services_name = "${var.unique_variable_name_suffix}-aiservices-${var.project_name}"

  # Deploy GPT-4 Turbo
  deploy_gpt4            = true
  gpt4_deployment_name   = "o4-mini"
  gpt4_model_name        = "o4-mini"
  gpt4_model_version     = "2025-04-16"
  gpt4_capacity          = 10

  # Deploy embeddings model
  deploy_embedding          = true
  embedding_deployment_name = "text-embedding-ada-002"
  embedding_model_name      = "text-embedding-ada-002"
  embedding_model_version   = "2"
  embedding_capacity        = 10

  tags = var.tags
}

# Role Assignment for being able to upload blobs
resource "azurerm_role_assignment" "blob_contrib" {
  scope                = module.storage.storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}