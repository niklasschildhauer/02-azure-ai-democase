variable "name" {
  description = "Name of the Azure OpenAI service"
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

variable "sku_name" {
  description = "SKU for Azure OpenAI"
  type        = string
  default     = "S0"
}

variable "deploy_gpt4" {
  description = "Deploy chat completion model"
  type        = bool
  default     = true
}

variable "gpt4_deployment_name" {
  description = "Name of the chat model deployment"
  type        = string
  default     = "gpt-5-mini"
}

variable "gpt4_model_name" {
  description = "Chat completion model name"
  type        = string
  default     = "gpt-5-mini"
}

variable "gpt4_model_version" {
  description = "Chat completion model version"
  type        = string
  default     = "2025-08-07"
}

variable "gpt4_capacity" {
  description = "Chat model capacity (tokens per minute / 1000)"
  type        = number
  default     = 10
}

variable "deploy_embedding" {
  description = "Deploy text-embedding model"
  type        = bool
  default     = true
}

variable "embedding_deployment_name" {
  description = "Name of the embedding deployment"
  type        = string
  default     = "text-embedding-3-small"
}

variable "embedding_model_name" {
  description = "Embedding model name"
  type        = string
  default     = "text-embedding-3-small"
}

variable "embedding_model_version" {
  description = "Embedding model version"
  type        = string
  default     = "1"
}

variable "embedding_capacity" {
  description = "Embedding capacity (tokens per minute / 1000)"
  type        = number
  default     = 10
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
