###############################################################################
# Unified Bootstrap Infrastructure
# Creates shared resources for all workshops:
# - Storage Account for Terraform state
# - User-Assigned Managed Identities with OIDC for GitHub Actions
# - Non-prod ACR (shared by dev and staging across all workshops)
###############################################################################

terraform {
  required_version = ">= 1.10.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.14"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 3.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
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

provider "azuread" {}

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
  description = "Unique suffix for resources that need a globally unique name in Azure (i.E. your name)"
  type        = string
  default     = ""
}

locals {
  resource_group_name  = "rg-${var.project_name}-shared"
  storage_account_name = "${var.unique_variable_name_suffix}cc${var.project_name}tfstate"

  common_tags = {
    Project     = var.project_name
    ManagedBy   = "Terraform"
    Environment = "bootstrap"
    Purpose     = "Shared infrastructure for all workshops"
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
# User-Assigned Managed Identities for GitHub Actions OIDC
# One identity per environment, shared across all workshops
###############################################################################

resource "azurerm_user_assigned_identity" "github_actions" {
  name                = "id-${var.project_name}-github"
  resource_group_name = azurerm_resource_group.shared.name
  location            = azurerm_resource_group.shared.location
  tags = merge(local.common_tags, {
    Purpose     = "GitHub Actions OIDC - All workshops"
  })
}

###############################################################################
# Federated Identity Credentials for GitHub Actions
###############################################################################

# Federated credential for pull requests (plan operations)
resource "azurerm_federated_identity_credential" "github_pr" {
  name                = "github-pr"
  resource_group_name = azurerm_resource_group.shared.name
  parent_id           = azurerm_user_assigned_identity.github_actions.id
  audience            = ["api://AzureADTokenExchange"]
  issuer              = "https://token.actions.githubusercontent.com"
  subject             = "repo:${var.github_org}/${var.github_repo}:pull_request"
}

# Federated credential for GitHub Environment (apply operations)
resource "azurerm_federated_identity_credential" "github_environment" {

  name                = "github-creds"
  resource_group_name = azurerm_resource_group.shared.name
  parent_id           = azurerm_user_assigned_identity.github_actions.id
  audience            = ["api://AzureADTokenExchange"]
  issuer              = "https://token.actions.githubusercontent.com"
  subject             = "repo:${var.github_org}/${var.github_repo}"
}

###############################################################################
# Role Assignments for Managed Identities
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

# Azure Kubernetes Service RBAC Cluster Admin for kubectl access
resource "azurerm_role_assignment" "aks_cluster_admin" {
  scope                = data.azurerm_subscription.current.id
  role_definition_name = "Azure Kubernetes Service RBAC Cluster Admin"
  principal_id         = azurerm_user_assigned_identity.github_actions.principal_id
}

###############################################################################
# Non-Prod ACR (Shared by Dev and Staging across all workshops)
###############################################################################

# resource "azurerm_container_registry" "nonprod" {
#   name                          = "${var.unique_variable_name_suffix}acrccworkshopnonprod"
#   resource_group_name           = azurerm_resource_group.shared.name
#   location                      = azurerm_resource_group.shared.location
#   sku                           = "Standard"
#   admin_enabled                 = false
#   public_network_access_enabled = true

#   tags = merge(local.common_tags, {
#     Purpose = "Non-production container registry for dev and staging"
#   })
# }

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
    managed_identities = {
        client_id    = azurerm_user_assigned_identity.github_actions.client_id
        principal_id = azurerm_user_assigned_identity.github_actions.principal_id
    }
    # nonprod_acr = {
    #   name         = azurerm_container_registry.nonprod.name
    #   id           = azurerm_container_registry.nonprod.id
    #   login_server = azurerm_container_registry.nonprod.login_server
    # }
  })
}

###############################################################################
# Outputs
###############################################################################

output "resource_group_name" {
  description = "Name of the shared resource group"
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

output "managed_identity_client_ids" {
  description = "Client IDs of the managed identities for GitHub Actions"
  value = azurerm_user_assigned_identity.github_actions.client_id
}

output "managed_identity_principal_ids" {
  description = "Principal IDs of the managed identities"
  value = azurerm_user_assigned_identity.github_actions.principal_id
}

output "tenant_id" {
  description = "Azure AD Tenant ID"
  value       = data.azurerm_client_config.current.tenant_id
}

output "subscription_id" {
  description = "Azure Subscription ID"
  value       = data.azurerm_subscription.current.subscription_id
}

# output "nonprod_acr_name" {
#   description = "Name of the non-prod ACR"
#   value       = azurerm_container_registry.nonprod.name
# }

# output "nonprod_acr_id" {
#   description = "ID of the non-prod ACR"
#   value       = azurerm_container_registry.nonprod.id
# }

# output "nonprod_acr_login_server" {
#   description = "Login server URL of the non-prod ACR"
#   value       = azurerm_container_registry.nonprod.login_server
# }

output "github_actions_configuration" {
  description = "GitHub Actions configuration instructions"
  value       = <<-EOT

    ============================================================
    GitHub Configuration Instructions
    ============================================================

    1. CREATE GITHUB ENVIRONMENTS (Settings -> Environments):
       - dev      (no protection rules)
       - staging  (1 required reviewer recommended)
       - prod     (1 required reviewer recommended)

    2. REPOSITORY SECRETS (Settings -> Secrets -> Actions):
       AZURE_TENANT_ID: ${data.azurerm_client_config.current.tenant_id}
       AZURE_SUBSCRIPTION_ID: ${data.azurerm_subscription.current.subscription_id}

    3. ENVIRONMENT SECRETS (Settings -> Environments -> <env> -> Secrets):

      environment:
         AZURE_CLIENT_ID: ${azurerm_user_assigned_identity.github_actions.client_id}

    These credentials work for ALL workflows across ALL workshops:
    - AKS-workshop-1
    - ContainerApp-workshop-2
    - Data-workshop-3

    ============================================================
  EOT
}

output "backend_config" {
  description = "Backend configuration for workshop environments"
  value       = <<-EOT

    ============================================================
    Terraform Backend Configuration
    ============================================================

    Use these values in each workshop's backend.tfvars:

    resource_group_name  = "${azurerm_resource_group.shared.name}"
    storage_account_name = "${azurerm_storage_account.tfstate.name}"
    container_name       = "${azurerm_storage_container.tfstate.name}"
    use_oidc             = true

    State file keys by workshop/environment:
    - AKS-workshop-1:        aks-{env}.tfstate
    - ContainerApp-workshop-2: containerapp-{env}.tfstate
    - Data-workshop-3:       data-{env}.tfstate

    ============================================================
  EOT
}
