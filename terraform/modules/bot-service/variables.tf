variable "name" {
  description = "Name of the Bot Service"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "sku" {
  description = "SKU for Bot Service"
  type        = string
  default     = "F0"
}

variable "display_name" {
  description = "Display name for the bot"
  type        = string
  default     = "T&C Assistant"
}

variable "messaging_endpoint" {
  description = "HTTPS endpoint for the bot's messaging API"
  type        = string
}

variable "bot_identity_id" {
  description = "Resource ID of the pre-created user-assigned managed identity"
  type        = string
}

variable "bot_identity_client_id" {
  description = "Client ID of the pre-created user-assigned managed identity"
  type        = string
}

variable "bot_identity_tenant_id" {
  description = "Tenant ID of the pre-created user-assigned managed identity"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
