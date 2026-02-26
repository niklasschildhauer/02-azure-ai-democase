variable "name" {
  description = "Name of the Azure AI Search service"
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

variable "sku" {
  description = "SKU for Azure AI Search"
  type        = string
  default     = "basic"
}

variable "semantic_search_sku" {
  description = "SKU for semantic search capability"
  type        = string
  default     = "standard"
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
