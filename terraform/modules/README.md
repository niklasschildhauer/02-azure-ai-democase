# Terraform Modules

This directory contains modular Terraform configurations for the Azure AI document processing infrastructure.

## Current Deployment

The active modules in `../main.tf` create an automated insurance claim processing pipeline:

```
modules/
├── storage/                    # ✅ ACTIVE - Blob storage for PDFs and results
├── document-intelligence/      # ✅ ACTIVE - PDF OCR and data extraction
├── function-app/               # ✅ ACTIVE - Serverless blob-triggered processing
├── key-vault/                  # Available but not currently used
├── search/                     # Available but not currently used
├── openai/                     # Available but not currently used
├── ai-services/                # ✅ ACTIVE - AI Services with GPT-4 and embeddings
└── monitoring/                 # Available but not currently used
```

## Active Modules

### 1. Storage Module (`storage/`) ✅

Manages Azure Blob Storage for claim documents and processed data.

**Resources Created:**
- Storage Account (StorageV2, LRS)
- Container: `insurance-claims` (for PDF uploads - triggers function)
- Container: `processed-data` (for JSON results from processing)
- Blob versioning enabled
- Soft delete retention (7 days)

**Key Variables:**
- `storage_account_name` - Storage account name (e.g., `dmstfrauddetect`)
- `claims_container_name` - Input container (default: `insurance-claims`)
- `processed_container_name` - Output container (default: `processed-data`)
- `enable_versioning` - Enable blob versioning (default: `true`)
- `retention_days` - Soft delete retention (default: `7`)

**Outputs:**
- `storage_account_id` - Resource ID for RBAC assignments
- `storage_account_name` - Account name for CLI operations
- `primary_connection_string` - Connection string (sensitive)
- `claims_container_name` - Input container name
- `processed_container_name` - Output container name

**Usage in main.tf:**
```hcl
module "storage" {
  source = "./modules/storage"

  storage_account_name = "dmst${var.project_name}"
  resource_group_name  = azurerm_resource_group.rg.name
  location             = var.location

  tags = var.tags
}
```

### 2. Document Intelligence Module (`document-intelligence/`) ✅

Deploys Azure AI Document Intelligence for PDF data extraction.

**Resources Created:**
- Cognitive Services Account (kind: `FormRecognizer`)
- Free tier (F0) - 500 pages/month included

**Capabilities:**
- OCR (Optical Character Recognition)
- Layout analysis (paragraphs, tables, structure)
- Key-value pair extraction (form fields)
- Table data extraction
- Prebuilt models (invoices, receipts, IDs, etc.)

**Key Variables:**
- `name` - Service name (e.g., `doc-intel-frauddetect`)
- `sku_name` - SKU tier (default: `F0` - free tier)
- `resource_group_name` - Resource group
- `location` - Azure region

**Outputs:**
- `id` - Resource ID for RBAC
- `endpoint` - API endpoint URL
- `primary_access_key` - API key (sensitive)
- `name` - Service name

**Usage in main.tf:**
```hcl
module "document_intelligence" {
  source = "./modules/document-intelligence"

  name                = "doc-intel-${var.project_name}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = var.location

  tags = var.tags
}
```

### 3. Function App Module (`function-app/`) ✅

Deploys Azure Function App with blob trigger for automatic document processing.

**Resources Created:**
- **Storage Account** (for Function App internals - separate from data storage)
- **Application Insights** (monitoring and telemetry)
- **App Service Plan** (Consumption/Y1 - serverless, pay-per-execution)
- **Linux Function App** (Python 3.12 runtime)
- **RBAC Role Assignments**:
  - Storage Blob Data Contributor on data storage
  - Cognitive Services User on Document Intelligence

**Key Variables:**
- `function_app_name` - Function App name (e.g., `func-frauddetect`)
- `service_plan_name` - App Service Plan name
- `function_storage_name` - Internal storage for function (e.g., `stfuncfrauddetect`)
- `app_insights_name` - Application Insights name
- `data_storage_connection_string` - Connection string for claim storage
- `doc_intelligence_endpoint` - Document Intelligence API endpoint
- `doc_intelligence_key` - Document Intelligence API key
- `input_container_name` - Blob trigger watches this container
- `output_container_name` - Function writes results here

**Outputs:**
- `function_app_id` - Function App resource ID
- `function_app_name` - Function App name for deployment
- `function_app_principal_id` - Managed identity principal ID
- `application_insights_instrumentation_key` - App Insights key (sensitive)

**Usage in main.tf:**
```hcl
module "function_app" {
  source = "./modules/function-app"

  function_app_name     = "func-${var.project_name}"
  service_plan_name     = "plan-${var.project_name}"
  function_storage_name = "stfunc${var.project_name}"
  app_insights_name     = "appi-${var.project_name}"

  resource_group_name = azurerm_resource_group.rg.name
  location            = var.location

  # Wire up data storage
  data_storage_connection_string = module.storage.primary_connection_string
  data_storage_account_id        = module.storage.storage_account_id

  # Wire up Document Intelligence
  doc_intelligence_endpoint = module.document_intelligence.endpoint
  doc_intelligence_key      = module.document_intelligence.primary_access_key
  doc_intelligence_id       = module.document_intelligence.id

  # Container configuration
  input_container_name  = module.storage.claims_container_name
  output_container_name = module.storage.processed_container_name

  tags = var.tags

  depends_on = [
    module.storage,
    module.document_intelligence
  ]
}
```

## How The Modules Work Together

```
┌─────────────────────────────────────────────────────────────┐
│  User uploads claim.pdf to insurance-claims container       │
└────────────────────┬────────────────────────────────────────┘
                     │ (Blob Storage - storage module)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Blob trigger fires → Azure Function starts automatically   │
└────────────────────┬────────────────────────────────────────┘
                     │ (Function App - function-app module)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Function calls Document Intelligence API                   │
│  Extracts: text, tables, key-value pairs                    │
└────────────────────┬────────────────────────────────────────┘
                     │ (Document Intelligence - doc-intel module)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Function performs fraud detection logic                    │
│  Checks: date mismatches, urgent language, etc.             │
└────────────────────┬────────────────────────────────────────┘
                     │ (Python code in function-app/)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Function saves claim_analyzed.json to processed-data       │
└─────────────────────────────────────────────────────────────┘
                     │ (Blob Storage - storage module)
                     ▼
                  Complete!
```

## Resource Dependencies

```
azurerm_resource_group (main.tf)
  │
  ├─► module.storage
  │     └─► Creates: dmstfrauddetect storage account
  │           ├─► insurance-claims container
  │           └─► processed-data container
  │
  ├─► module.document_intelligence
  │     └─► Creates: doc-intel-frauddetect cognitive service
  │
  └─► module.function_app
        ├─► Requires: module.storage outputs (connection string, container names)
        ├─► Requires: module.document_intelligence outputs (endpoint, key)
        └─► Creates:
              ├─► stfuncfrauddetect (function internal storage)
              ├─► appi-frauddetect (Application Insights)
              ├─► plan-frauddetect (Consumption plan)
              ├─► func-frauddetect (Function App)
              └─► RBAC role assignments (managed identity permissions)
```

## Deployed Resources Summary

When you run `terraform apply`, these Azure resources are created:

| Resource Type | Name Pattern | Purpose |
|--------------|--------------|---------|
| Resource Group | `rg-{project_name}` | Container for all resources |
| Storage Account (data) | `dmst{project_name}` | Claim PDFs and results |
| Blob Container | `insurance-claims` | Input: PDF uploads trigger processing |
| Blob Container | `processed-data` | Output: JSON results from function |
| Cognitive Account | `doc-intel-{project_name}` | Document Intelligence API |
| Storage Account (func) | `stfunc{project_name}` | Function App internals |
| Application Insights | `appi-{project_name}` | Function monitoring |
| App Service Plan | `plan-{project_name}` | Serverless consumption plan |
| Function App | `func-{project_name}` | Blob-triggered processing |

**Default project_name**: `frauddetect`

## Testing Modules

Validate configuration:

```bash
# From terraform/ directory
terraform validate

# Initialize and plan
terraform init -backend-config=backend.tfvars
terraform plan

# Apply configuration
terraform apply
```

Verify resources:

```bash
# Check storage containers
az storage container list \
  --account-name dmstfrauddetect \
  --auth-mode login

# Check Document Intelligence
az cognitiveservices account show \
  --name doc-intel-frauddetect \
  --resource-group rg-frauddetect

# Check Function App
az functionapp show \
  --name func-frauddetect \
  --resource-group rg-frauddetect
```

## Module Best Practices

### 1. Consistent Naming
All modules use the pattern: `{type}-{project_name}`
- Storage: `dmst{project_name}` (no hyphens due to storage naming rules)
- Other services: `{abbreviation}-{project_name}`

### 2. Module Output Chaining
Outputs from one module feed into another:
```hcl
# Storage module output
output "primary_connection_string" { ... }

# Function module uses it
data_storage_connection_string = module.storage.primary_connection_string
```

### 3. RBAC with Managed Identity
Function App uses system-assigned managed identity instead of keys:
```hcl
# Function App has automatic permissions via RBAC
resource "azurerm_role_assignment" "function_storage_blob_contributor" {
  scope                = var.data_storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_linux_function_app.processor.identity[0].principal_id
}
```

### 4. Sensitive Outputs
API keys and connection strings are marked sensitive:
```hcl
output "primary_access_key" {
  value     = azurerm_cognitive_account.doc_intelligence.primary_access_key
  sensitive = true
}
```

## Extending The Solution

Want to add more modules? Here are common extensions:

### Add Azure AI Search (search module)
- Index extracted claim data
- Enable semantic search across claims
- Detect patterns and similarities

### Add Azure OpenAI (openai module)
- GPT-4 for advanced fraud reasoning
- Embeddings for vector similarity
- Natural language explanations

### Add Key Vault (key-vault module)
- Store secrets securely
- Reference in Function App settings
- Rotate keys automatically

All these modules are available in this directory and can be enabled by uncommenting them in `../main.tf`.

## Additional Resources

- [Terraform Module Documentation](https://www.terraform.io/docs/language/modules/)
- [Azure Provider Documentation](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Azure Functions + Terraform](https://learn.microsoft.com/azure/azure-functions/functions-infrastructure-as-code)
- [Document Intelligence SDK](https://learn.microsoft.com/azure/ai-services/document-intelligence/quickstarts/get-started-sdks-rest-api)
