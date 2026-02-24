# Azure Function App Module
# Provides serverless document processing with blob trigger

# Storage Account for Function App internals (required by Azure Functions)
resource "azurerm_storage_account" "function_storage" {
  name                     = var.function_storage_name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"

  tags = var.tags
}

# Application Insights for Function monitoring
resource "azurerm_application_insights" "function_insights" {
  name                = var.app_insights_name
  resource_group_name = var.resource_group_name
  location            = var.location
  application_type    = "other"

  tags = var.tags
}

# App Service Plan (Consumption tier for serverless)
resource "azurerm_service_plan" "function_plan" {
  name                = var.service_plan_name
  resource_group_name = var.resource_group_name
  location            = var.location
  os_type             = "Linux"
  sku_name            = var.sku_name

  tags = var.tags
}

# Linux Function App
resource "azurerm_linux_function_app" "processor" {
  name                       = var.function_app_name
  resource_group_name        = var.resource_group_name
  location                   = var.location
  service_plan_id            = azurerm_service_plan.function_plan.id
  storage_account_name       = azurerm_storage_account.function_storage.name
  storage_account_access_key = azurerm_storage_account.function_storage.primary_access_key

  identity {
    type = "SystemAssigned"
  }

  site_config {
    application_stack {
      python_version = var.python_version
    }

    application_insights_key               = azurerm_application_insights.function_insights.instrumentation_key
    application_insights_connection_string = azurerm_application_insights.function_insights.connection_string
  }

  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME"       = "python"
    "AzureWebJobsFeatureFlags"       = "EnableWorkerIndexing"
    "PYTHON_ENABLE_WORKER_EXTENSIONS" = "1"

    # Data Storage Account (where claims PDFs are stored)
    "DataStorageConnection" = var.data_storage_connection_string

    # Document Intelligence Configuration
    "DOCUMENT_INTELLIGENCE_ENDPOINT" = var.doc_intelligence_endpoint
    "DOCUMENT_INTELLIGENCE_KEY"      = var.doc_intelligence_key

    # Container names
    "INPUT_CONTAINER_NAME"  = var.input_container_name
    "OUTPUT_CONTAINER_NAME" = var.output_container_name
  }

  tags = var.tags
}

# RBAC: Grant Function App access to read/write blobs on data storage account
resource "azurerm_role_assignment" "function_storage_blob_contributor" {
  scope                = var.data_storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_linux_function_app.processor.identity[0].principal_id
}

# RBAC: Grant Function App access to Document Intelligence
resource "azurerm_role_assignment" "function_cognitive_user" {
  scope                = var.doc_intelligence_id
  role_definition_name = "Cognitive Services User"
  principal_id         = azurerm_linux_function_app.processor.identity[0].principal_id
}
