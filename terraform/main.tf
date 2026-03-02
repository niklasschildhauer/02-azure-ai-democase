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

# Resource Group
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

# AI Services Module (multi-service, required for skillset billing)
module "ai_services" {
  source = "./modules/ai-services"

  name                = "${var.unique_variable_name_suffix}-ais-${var.project_name}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = var.location

  tags = var.tags
}

# OpenAI Module
module "openai" {
  source = "./modules/openai"

  name                = "${var.unique_variable_name_suffix}-oai-${var.project_name}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = var.openai_location

  tags = var.tags
}

# Azure AI Search Module
module "search" {
  source = "./modules/search"

  name                = "${var.unique_variable_name_suffix}-srch-${var.project_name}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = var.location
  sku                 = var.search_sku

  tags = var.tags
}

# Bot Identity (created standalone to break circular dependency:
# function_app needs identity at creation, bot_service needs function_app hostname)
resource "azurerm_user_assigned_identity" "bot_identity" {
  name                = "${var.unique_variable_name_suffix}-bot-${var.project_name}-identity"
  resource_group_name = azurerm_resource_group.rg.name
  location            = var.location

  tags = var.tags
}

# Bot Service Module (created after function_app so it can reference the hostname)
module "bot_service" {
  source = "./modules/bot-service"

  name                = "${var.unique_variable_name_suffix}-bot-${var.project_name}"
  resource_group_name = azurerm_resource_group.rg.name
  messaging_endpoint  = "https://${module.function_app.function_app_default_hostname}/api/messages"

  bot_identity_id        = azurerm_user_assigned_identity.bot_identity.id
  bot_identity_client_id = azurerm_user_assigned_identity.bot_identity.client_id
  bot_identity_tenant_id = azurerm_user_assigned_identity.bot_identity.tenant_id

  tags = var.tags

  depends_on = [module.function_app]
}

# Function App Module (Blob Trigger for Document Processing + RAG Chatbot)
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

  # Container names
  input_container_name  = module.storage.claims_container_name
  output_container_name = module.storage.processed_container_name

  # OpenAI configuration
  openai_endpoint             = module.openai.endpoint
  openai_chat_deployment      = module.openai.gpt4_deployment_name
  openai_embedding_deployment = module.openai.embedding_deployment_name
  openai_id                   = module.openai.id

  # Search configuration
  search_endpoint = module.search.endpoint
  search_id       = module.search.id

  # Bot identity (standalone resource, not from bot_service module)
  bot_identity_id        = azurerm_user_assigned_identity.bot_identity.id
  bot_identity_client_id = azurerm_user_assigned_identity.bot_identity.client_id
  bot_identity_tenant_id = azurerm_user_assigned_identity.bot_identity.tenant_id

  tags = var.tags

  depends_on = [
    module.storage,
    module.document_intelligence,
    module.openai,
    module.search
  ]
}

# Role Assignment for being able to upload blobs
resource "azurerm_role_assignment" "blob_contrib" {
  scope                = module.storage.storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

# RBAC: Search -> Storage (indexer reads T&C PDFs)
resource "azurerm_role_assignment" "search_blob_reader" {
  scope                = module.storage.storage_account_id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = module.search.principal_id
}

# RBAC: Search -> OpenAI (embedding skill)
resource "azurerm_role_assignment" "search_openai_user" {
  scope                = module.openai.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = module.search.principal_id
}

# RBAC: Search -> Document Intelligence (Document Layout skill)
resource "azurerm_role_assignment" "search_doc_intel_user" {
  scope                = module.document_intelligence.id
  role_definition_name = "Cognitive Services User"
  principal_id         = module.search.principal_id
}

# RBAC: Search -> AI Services (skillset billing)
resource "azurerm_role_assignment" "search_ai_services_user" {
  scope                = module.ai_services.id
  role_definition_name = "Cognitive Services User"
  principal_id         = module.search.principal_id
}