variable "storage_account_name" {
  description = "Name of the storage account"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "account_tier" {
  description = "Storage account tier"
  type        = string
  default     = "Standard"
}

variable "replication_type" {
  description = "Storage replication type"
  type        = string
  default     = "LRS"
}

variable "enable_versioning" {
  description = "Enable blob versioning"
  type        = bool
  default     = true
}

variable "retention_days" {
  description = "Blob soft delete retention days"
  type        = number
  default     = 7
}

variable "claims_container_name" {
  description = "Name of the claims blob container"
  type        = string
  default     = "insurance-claims"
}

variable "processed_container_name" {
  description = "Name of the processed data blob container"
  type        = string
  default     = "processed-data"
}

variable "terms_container_name" {
  description = "Name of the terms and conditions blob container"
  type        = string
  default     = "terms-and-conditions"
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
