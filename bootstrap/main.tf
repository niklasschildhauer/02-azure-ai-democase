###############################################################################
# Bootstrap Infrastructure — Azure AI Demo Case
# Creates:
# - Resource group for shared/bootstrap resources
# - Storage account for Terraform remote state
# - User-assigned managed identity with OIDC for GitHub Actions
# - Federated credentials for PR (plan) and main branch (apply)
# - Role assignments for CI/CD operations
###############################################################################

terraform {
  required_version = ">= 1.10.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.14"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = false
    }
  }
  subscription_id     = var.subscription_id
  storage_use_azuread = true
}

provider "github" {
  owner = var.github_org
  token = var.github_token # Can also use GITHUB_TOKEN env var
}

###############################################################################
# Variables
###############################################################################

variable "subscription_id" {
  description = "Azure Subscription ID"
  type        = string
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "germanywestcentral"
}

variable "project_name" {
  description = "Project name used in resource naming"
  type        = string
  default     = "ccworkshop"
}

variable "github_org" {
  description = "GitHub organization name"
  type        = string
  default     = "codecentric"
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = "azure-casestudies"
}

variable "unique_variable_name_suffix" {
  description = "Unique suffix for globally unique Azure resource names (e.g. your initials)"
  type        = string
}

variable "github_token" {
  description = "GitHub PAT with 'repo' scope. Can also use GITHUB_TOKEN env var."
  type        = string
  sensitive   = true
  default     = null
}

locals {
  resource_group_name  = "rg-${var.project_name}-shared"
  storage_account_name = "${var.unique_variable_name_suffix}cc${var.project_name}tfstate"

  common_tags = {
    Project     = var.project_name
    ManagedBy   = "Terraform"
    Environment = "bootstrap"
  }
}

###############################################################################
# Data Sources
###############################################################################

data "azurerm_subscription" "current" {}

data "azurerm_client_config" "current" {}

###############################################################################
# Resource Group
###############################################################################

resource "azurerm_resource_group" "shared" {
  name     = local.resource_group_name
  location = var.location
  tags     = local.common_tags
}

###############################################################################
# Storage Account for Terraform State
###############################################################################

resource "azurerm_storage_account" "tfstate" {
  name                            = local.storage_account_name
  resource_group_name             = azurerm_resource_group.shared.name
  location                        = azurerm_resource_group.shared.location
  account_tier                    = "Standard"
  account_replication_type        = "GRS"
  min_tls_version                 = "TLS1_2"
  shared_access_key_enabled       = false
  public_network_access_enabled   = true
  allow_nested_items_to_be_public = false

  blob_properties {
    versioning_enabled = true

    delete_retention_policy {
      days = 30
    }

    container_delete_retention_policy {
      days = 30
    }
  }

  tags = local.common_tags
}

resource "azurerm_storage_container" "tfstate" {
  name                  = "tfstate"
  storage_account_id    = azurerm_storage_account.tfstate.id
  container_access_type = "private"
}

###############################################################################
# User-Assigned Managed Identity for GitHub Actions OIDC
###############################################################################

resource "azurerm_user_assigned_identity" "github_actions" {
  name                = "id-${var.project_name}-github"
  resource_group_name = azurerm_resource_group.shared.name
  location            = azurerm_resource_group.shared.location
  tags                = local.common_tags
}

###############################################################################
# Federated Identity Credentials for GitHub Actions
###############################################################################

# Federated credential for pull requests (plan operations)
resource "azurerm_federated_identity_credential" "github_pr" {
  name      = "github-pr"
  parent_id = azurerm_user_assigned_identity.github_actions.id
  audience  = ["api://AzureADTokenExchange"]
  issuer    = "https://token.actions.githubusercontent.com"
  subject   = "repo:${var.github_org}/${var.github_repo}:pull_request"
}

# Federated credential for main branch (apply operations)
resource "azurerm_federated_identity_credential" "github_main" {
  name      = "github-main"
  parent_id = azurerm_user_assigned_identity.github_actions.id
  audience  = ["api://AzureADTokenExchange"]
  issuer    = "https://token.actions.githubusercontent.com"
  subject   = "repo:${var.github_org}/${var.github_repo}:ref:refs/heads/main"
}

###############################################################################
# Role Assignments
###############################################################################

# Storage Blob Data Contributor on state storage account
resource "azurerm_role_assignment" "tfstate_blob" {
  scope                = azurerm_storage_account.tfstate.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.github_actions.principal_id
}

# Contributor role at subscription level for resource management
resource "azurerm_role_assignment" "subscription_contributor" {
  scope                = data.azurerm_subscription.current.id
  role_definition_name = "Contributor"
  principal_id         = azurerm_user_assigned_identity.github_actions.principal_id
}

# User Access Administrator for managing RBAC
resource "azurerm_role_assignment" "subscription_uaa" {
  scope                = data.azurerm_subscription.current.id
  role_definition_name = "User Access Administrator"
  principal_id         = azurerm_user_assigned_identity.github_actions.principal_id
}

###############################################################################
# GitHub Actions Variables
###############################################################################

resource "github_actions_variable" "azure_client_id" {
  repository    = var.github_repo
  variable_name = "AZURE_CLIENT_ID"
  value         = azurerm_user_assigned_identity.github_actions.client_id
}

resource "github_actions_variable" "azure_tenant_id" {
  repository    = var.github_repo
  variable_name = "AZURE_TENANT_ID"
  value         = data.azurerm_client_config.current.tenant_id
}

resource "github_actions_variable" "azure_subscription_id" {
  repository    = var.github_repo
  variable_name = "AZURE_SUBSCRIPTION_ID"
  value         = data.azurerm_subscription.current.subscription_id
}

resource "github_actions_variable" "storage_account_name" {
  repository    = var.github_repo
  variable_name = "STORAGE_ACCOUNT_NAME"
  value         = azurerm_storage_account.tfstate.name
}

resource "github_actions_variable" "unique_suffix" {
  repository    = var.github_repo
  variable_name = "UNIQUE_SUFFIX"
  value         = var.unique_variable_name_suffix
}

###############################################################################
# Output File
###############################################################################

resource "local_file" "bootstrap_output" {
  filename = "${path.module}/bootstrap-output.json"
  content = jsonencode({
    tenant_id            = data.azurerm_client_config.current.tenant_id
    subscription_id      = data.azurerm_subscription.current.subscription_id
    resource_group_name  = azurerm_resource_group.shared.name
    storage_account_name = azurerm_storage_account.tfstate.name
    storage_container    = azurerm_storage_container.tfstate.name
    managed_identity = {
      client_id    = azurerm_user_assigned_identity.github_actions.client_id
      principal_id = azurerm_user_assigned_identity.github_actions.principal_id
    }
  })
}

###############################################################################
# Outputs
###############################################################################

output "resource_group_name" {
  description = "Name of the bootstrap resource group"
  value       = azurerm_resource_group.shared.name
}

output "storage_account_name" {
  description = "Name of the storage account for Terraform state"
  value       = azurerm_storage_account.tfstate.name
}

output "storage_container_name" {
  description = "Name of the blob container for Terraform state"
  value       = azurerm_storage_container.tfstate.name
}

output "managed_identity_client_id" {
  description = "Client ID of the managed identity for GitHub Actions"
  value       = azurerm_user_assigned_identity.github_actions.client_id
}

output "managed_identity_principal_id" {
  description = "Principal ID of the managed identity"
  value       = azurerm_user_assigned_identity.github_actions.principal_id
}

output "tenant_id" {
  description = "Azure AD Tenant ID"
  value       = data.azurerm_client_config.current.tenant_id
}

output "subscription_id" {
  description = "Azure Subscription ID"
  value       = data.azurerm_subscription.current.subscription_id
}

output "github_actions_configuration" {
  description = "GitHub Actions configuration instructions"
  value       = <<-EOT

    ============================================================
    GitHub Configuration - AUTO-CONFIGURED
    ============================================================

    The following variables have been automatically created
    in ${var.github_org}/${var.github_repo}:

    VARIABLES:
      - AZURE_CLIENT_ID
      - AZURE_TENANT_ID
      - AZURE_SUBSCRIPTION_ID
      - STORAGE_ACCOUNT_NAME
      - UNIQUE_SUFFIX

    Verify at: https://github.com/${var.github_org}/${var.github_repo}/settings/variables/actions

    ============================================================
  EOT
}

output "backend_config" {
  description = "Terraform backend configuration for terraform/backend.tfvars"
  value       = <<-EOT

    ============================================================
    Terraform Backend Configuration
    ============================================================

    Already committed in terraform/backend.tfvars.
    Only the storage_account_name is injected at init time.

    resource_group_name  = "${azurerm_resource_group.shared.name}"
    storage_account_name = "${azurerm_storage_account.tfstate.name}"
    container_name       = "${azurerm_storage_container.tfstate.name}"
    key                  = "ai-democase.tfstate"
    use_oidc             = true

    ============================================================
  EOT
}
