variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "function_app_name" {
  description = "Name of the Function App"
  type        = string
}

variable "service_plan_name" {
  description = "Name of the App Service Plan"
  type        = string
}

variable "function_storage_name" {
  description = "Name of the storage account for Function App internals"
  type        = string
}

variable "app_insights_name" {
  description = "Name of Application Insights"
  type        = string
}

variable "sku_name" {
  description = "SKU for App Service Plan"
  type        = string
  default     = "Y1" # Consumption plan

  validation {
    condition     = contains(["Y1", "EP1", "EP2", "EP3"], var.sku_name)
    error_message = "SKU must be Y1 (Consumption), EP1, EP2, or EP3 (Premium)."
  }
}

variable "python_version" {
  description = "Python version for Function App"
  type        = string
  default     = "3.11"
}

variable "data_storage_connection_string" {
  description = "Connection string for data storage account (where claims PDFs are)"
  type        = string
  sensitive   = true
}

variable "data_storage_account_id" {
  description = "Resource ID of the data storage account"
  type        = string
}

variable "doc_intelligence_endpoint" {
  description = "Document Intelligence endpoint URL"
  type        = string
}

variable "doc_intelligence_key" {
  description = "Document Intelligence API key"
  type        = string
  sensitive   = true
}

variable "doc_intelligence_id" {
  description = "Resource ID of Document Intelligence service"
  type        = string
}

variable "input_container_name" {
  description = "Name of the blob container for input PDFs"
  type        = string
  default     = "claims"
}

variable "output_container_name" {
  description = "Name of the blob container for processed results"
  type        = string
  default     = "processed"
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
