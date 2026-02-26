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

variable "openai_endpoint" {
  description = "Azure OpenAI endpoint URL"
  type        = string
  default     = ""
}

variable "openai_chat_deployment" {
  description = "Azure OpenAI chat model deployment name"
  type        = string
  default     = ""
}

variable "openai_embedding_deployment" {
  description = "Azure OpenAI embedding model deployment name"
  type        = string
  default     = ""
}

variable "openai_id" {
  description = "Resource ID of Azure OpenAI service"
  type        = string
  default     = ""
}

variable "search_endpoint" {
  description = "Azure AI Search endpoint URL"
  type        = string
  default     = ""
}

variable "search_index_name" {
  description = "Name of the search index for T&C documents"
  type        = string
  default     = "terms-and-conditions-index"
}

variable "search_id" {
  description = "Resource ID of Azure AI Search service"
  type        = string
  default     = ""
}

variable "bot_identity_id" {
  description = "Resource ID of the bot's user-assigned managed identity"
  type        = string
  default     = ""
}

variable "bot_identity_client_id" {
  description = "Client ID of the bot's managed identity"
  type        = string
  default     = ""
}

variable "bot_identity_tenant_id" {
  description = "Tenant ID of the bot's managed identity"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
