# Storage Account Module
# Provides blob storage for insurance claim PDFs and processed data

resource "azurerm_storage_account" "storage" {
  name                     = var.storage_account_name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = var.account_tier
  account_replication_type = var.replication_type
  account_kind             = "StorageV2"

  blob_properties {
    versioning_enabled = var.enable_versioning

    delete_retention_policy {
      days = var.retention_days
    }
  }

  tags = var.tags
}

# Blob Container for Insurance Claims PDFs
resource "azurerm_storage_container" "claims" {
  name                  = var.claims_container_name
  storage_account_id    = azurerm_storage_account.storage.id
  container_access_type = "private"
}

# Blob Container for Processed Data
resource "azurerm_storage_container" "processed" {
  name                  = var.processed_container_name
  storage_account_id    = azurerm_storage_account.storage.id
  container_access_type = "private"
}

# Blob Container for Terms and Conditions PDFs
resource "azurerm_storage_container" "terms_and_conditions" {
  name                  = var.terms_container_name
  storage_account_id    = azurerm_storage_account.storage.id
  container_access_type = "private"
}
