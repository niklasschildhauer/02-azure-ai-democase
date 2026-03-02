# Azure Bot Service Module
# Provides Bot Service with Web Chat channel for T&C Assistant
# NOTE: The bot's user-assigned identity is created externally and passed in
# to avoid circular dependencies (function_app needs the identity, bot needs the hostname).

# Azure Bot Service
resource "azurerm_bot_service_azure_bot" "bot" {
  name                = var.name
  resource_group_name = var.resource_group_name
  location            = "global"
  sku                 = var.sku
  display_name        = var.display_name

  microsoft_app_type      = "UserAssignedMSI"
  microsoft_app_id        = var.bot_identity_client_id
  microsoft_app_tenant_id = var.bot_identity_tenant_id
  microsoft_app_msi_id    = var.bot_identity_id

  endpoint = var.messaging_endpoint

  tags = var.tags
}