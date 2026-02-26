variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "frauddetect"

  validation {
    condition     = can(regex("^[a-z0-9]{3,12}$", var.project_name))
    error_message = "Project name must be 3-12 characters, lowercase letters and numbers only."
  }
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "swedencentral"
}

variable "openai_location" {
  description = "Azure region for OpenAI service (limited availability)"
  type        = string
  default     = "swedencentral"
}

variable "search_sku" {
  description = "Azure AI Search SKU"
  type        = string
  default     = "basic"

  validation {
    condition     = contains(["free", "basic", "standard", "standard2", "standard3"], var.search_sku)
    error_message = "Search SKU must be one of: free, basic, standard, standard2, standard3."
  }
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "Insurance Fraud Detection"
    Environment = "Development"
    ManagedBy   = "Terraform"
    Workshop    = "Azure AI Demo"
  }
}

variable "nonprod_acr_resource_group" {
  description = "Resource group of the non-prod ACR"
  type        = string
}

variable "unique_variable_name_suffix" {
  description = "Unique suffix for globally unique Azure resource names (must match bootstrap, max 4 chars due to Key Vault 24-char limit)"
  type        = string

  validation {
    condition     = length(var.unique_variable_name_suffix) >= 1 && length(var.unique_variable_name_suffix) <= 4
    error_message = "unique_variable_name_suffix must be 1-4 characters (Key Vault names have a 24-character limit)."
  }
}