# T&C RAG Chatbot — Change Log

All changes made to implement the Terms & Conditions RAG chatbot on top of the existing insurance fraud detection demo.

---

## Modified Files

### `terraform/modules/openai/main.tf`

Changed the `kind` attribute of the `azurerm_cognitive_account` resource from `"OpenAI"` to `"AIServices"`. The `"OpenAI"` kind is legacy; `"AIServices"` is the current resource type required by Azure for new Cognitive Services accounts that include OpenAI capabilities. Updated comments and resource description from "GPT-4" to generic "chat completion model" to reflect the model-agnostic naming.

### `terraform/modules/openai/variables.tf`

Updated six variable defaults to move from deprecated/outdated models to current ones. Also updated all variable descriptions from "GPT-4" to generic "chat completion model" / "chat model" since the actual model is now gpt-5-mini:

- **GPT deployment name**: `"gpt-4"` → `"gpt-5-mini"` (GA since Aug 2025, no registration required, retires Feb 2027)
- **GPT model name**: `"gpt-4"` → `"gpt-5-mini"` (cost-effective GPT-5 series model suitable for RAG workloads)
- **GPT model version**: `"turbo-2024-04-09"` → `"2025-08-07"` (gpt-5-mini release version)
- **Embedding deployment name**: `"text-embedding-ada-002"` → `"text-embedding-3-small"` (ada-002 deprecated Oct 2025)
- **Embedding model name**: `"text-embedding-ada-002"` → `"text-embedding-3-small"` (1536-dim model, better retrieval quality than ada-002 at lower cost than 3-large)
- **Embedding model version**: `"2"` → `"1"` (initial version of the text-embedding-3-small model)

### `terraform/modules/storage/main.tf`

Added a new `azurerm_storage_container` resource named `terms_and_conditions` after the existing `processed` container. This private container stores the insurance T&C PDF documents that the AI Search indexer will read and process for the RAG pipeline.

### `terraform/modules/storage/variables.tf`

Added a `terms_container_name` variable (type `string`, default `"terms-and-conditions"`) to make the new container name configurable, consistent with how `claims_container_name` and `processed_container_name` are already parameterized.

### `terraform/modules/storage/outputs.tf`

Added a `terms_container_name` output that exposes the new container's name, so the root `main.tf` and `outputs.tf` can reference it without hardcoding.

### `terraform/modules/function-app/main.tf`

Three distinct changes:

1. **Identity block** — Changed from a static `SystemAssigned` identity to a conditional that adds `UserAssigned` when a bot identity is provided. When `bot_identity_id` is non-empty, the type becomes `"SystemAssigned, UserAssigned"` and the bot's user-assigned managed identity is attached. This lets the Function App authenticate as the bot when receiving Bot Framework callbacks.

2. **App settings** — Added 8 new environment variables to the Function App's `app_settings` block: three for Azure OpenAI (`AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_CHAT_DEPLOYMENT`, `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`), two for Azure AI Search (`AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_INDEX_NAME`), and three for Bot Framework authentication (`MicrosoftAppId`, `MicrosoftAppTenantId`, `MicrosoftAppType`). All are wired from module variables.

3. **Two new RBAC role assignments** — Added `Cognitive Services OpenAI User` on the OpenAI resource and `Search Index Data Reader` on the AI Search resource, both granted to the Function App's system-assigned principal. Both use `count` guards so they only create when the respective resource IDs are non-empty, preserving backward compatibility if the modules aren't wired.

### `terraform/modules/function-app/variables.tf`

Added 11 new variables to support the chatbot integration. Grouped into three categories:

- **OpenAI** (4): `openai_endpoint`, `openai_chat_deployment`, `openai_embedding_deployment`, `openai_id`
- **Search** (3): `search_endpoint`, `search_index_name` (default `"terms-and-conditions-index"`), `search_id`
- **Bot identity** (4): `bot_identity_id`, `bot_identity_client_id`, `bot_identity_tenant_id`

All default to `""` so the existing fraud-detection-only deployment still works without providing them.

### `terraform/main.tf`

Five groups of changes:

1. **Three new module blocks** — Added `module "openai"`, `module "search"`, and `module "bot_service"`, each pointing to their respective `./modules/` source. OpenAI uses `var.openai_location`, Search uses `var.search_sku`, and Bot Service receives the Function App's messaging endpoint via `module.function_app.function_app_default_hostname`. Bot Service has `depends_on = [module.function_app]` because it needs the hostname.

2. **Standalone bot identity resource** — The bot's `azurerm_user_assigned_identity` is created directly in `main.tf` as a standalone resource, NOT inside the bot-service module. This breaks what would otherwise be a circular dependency: `function_app` needs the bot identity at creation time (for the UserAssigned identity block and app settings), while `bot_service` needs the function app's hostname (for the messaging endpoint). By extracting the identity, both modules can reference it independently without depending on each other.

3. **Extended `module "function_app"`** — Passed 9 new arguments (OpenAI endpoint/deployments/id, Search endpoint/id, Bot identity id/client_id/tenant_id from the standalone resource) and added `module.openai` and `module.search` to its `depends_on` list.

4. **Three cross-service RBAC assignments** — Added role assignments so the AI Search managed identity can: read blobs from storage (`Storage Blob Data Reader`), call OpenAI embeddings (`Cognitive Services OpenAI User`), and use Document Intelligence for the Document Layout skill (`Cognitive Services User`).

5. **Dependency graph** (verified cycle-free):
   ```
   azurerm_user_assigned_identity.bot_identity  (no deps)
        ↓                                  ↓
   module.function_app                module.bot_service
   (needs identity + openai/search)   (needs identity + function_app hostname)
                      ↘                ↙
                    depends_on = [function_app]
   ```

### `terraform/outputs.tf`

Added 8 new outputs for the newly provisioned resources: `openai_endpoint`, `openai_name`, `search_endpoint`, `search_name`, `search_admin_key` (marked sensitive), `bot_name`, `terms_container_name`, and `doc_intelligence_id`. Updated the `deployment_summary` map to include `terms_container`, `openai`, `search`, and `bot_service` alongside the existing entries.

### `function-app/function_app.py`

Extended the existing file (without modifying the `process_insurance_claim` blob trigger) with the full RAG chatbot functionality:

1. **New imports** — Added `traceback`, `AzureOpenAI`, `DefaultAzureCredential`/`ManagedIdentityCredential`, `SearchClient`, `VectorizableTextQuery`.

2. **New environment variable reads** — `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_CHAT_DEPLOYMENT`, `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_INDEX_NAME`, `MicrosoftAppId`, `MicrosoftAppTenantId`.

3. **System prompt constant** — A strict RAG prompt that instructs the model to only answer from provided T&C context, cite sections, never fabricate, and decline off-topic questions.

4. **Two separate credential helpers** — `get_service_credential()` returns `DefaultAzureCredential` which resolves to the Function App's system-assigned managed identity in Azure (used for OpenAI and Search calls where RBAC is assigned to the system identity). `get_bot_credential()` returns `ManagedIdentityCredential(client_id=BOT_APP_ID)` targeting the bot's user-assigned identity (used only for Bot Framework token acquisition). This separation is critical: the RBAC roles for OpenAI and Search are on the system-assigned principal, while Bot Framework authentication requires the bot's user-assigned identity.

5. **`search_terms_and_conditions(query)`** — Performs hybrid search (keyword + vector via `VectorizableTextQuery`) with semantic ranking against the T&C index. Uses `get_service_credential()`. Returns the top 5 chunks formatted as numbered source blocks.

6. **`get_rag_response(user_message)`** — Orchestrates the RAG pipeline: calls search, builds a system+user message pair with the retrieved context, calls Azure OpenAI chat completions (temperature 0.1, max 1024 tokens) using `get_service_credential()`, and returns the answer.

7. **`messages(req)` HTTP trigger** — Registered at `/api/messages` (POST, anonymous auth). Handles the Bot Framework Activity protocol directly: processes `message` activities through the RAG pipeline and sends replies via the Bot Framework service URL, handles `conversationUpdate` activities with a welcome message, and acknowledges all other activity types with 200. Bot Framework token acquisition uses `get_bot_credential()` to authenticate as the registered bot.

### `function-app/requirements.txt`

Added three new dependencies for the chatbot: `openai>=1.30.0` (Azure OpenAI SDK), `azure-search-documents>=11.6.0` (hybrid/semantic search client), and `requests>=2.31.0` (for sending Bot Framework reply activities via REST).

---

## New Files

### `terraform/modules/search/main.tf`

Defines a single `azurerm_search_service` resource with a system-assigned managed identity and configurable semantic search SKU. The identity is needed for the indexer to authenticate to blob storage, OpenAI, and Document Intelligence via RBAC rather than API keys.

### `terraform/modules/search/variables.tf`

Six variables for the search module: `name`, `resource_group_name`, `location`, `sku` (default `"basic"` — supports up to 15 indexes, sufficient for the demo), `semantic_search_sku` (default `"standard"` — enables semantic ranking), and `tags`.

### `terraform/modules/search/outputs.tf`

Six outputs: `id` and `name` (for RBAC scoping), `endpoint` (constructed as `https://<name>.search.windows.net`), `primary_key` and `query_key` (both sensitive, for the setup script), and `principal_id` (for cross-service RBAC assignments in `main.tf`).

### `terraform/modules/bot-service/main.tf`

Two resources (the bot's user-assigned identity is created externally in `main.tf` and passed in as variables to avoid a circular dependency):

1. **`azurerm_bot_service_azure_bot`** — The bot registration resource. Set to `location = "global"` (required by Azure Bot Service), uses `UserAssignedMSI` app type with the externally-provided identity, and points its messaging endpoint at the Function App's `/api/messages` URL.
2. **`azurerm_bot_channel_web_chat`** — Enables the Web Chat channel so agents can test the bot directly from the Azure Portal.

### `terraform/modules/bot-service/variables.tf`

Eight variables: `name`, `resource_group_name`, `sku` (default `"F0"` free tier), `display_name` (default `"T&C Assistant"`), `messaging_endpoint` (the Function App HTTPS URL), `bot_identity_id`, `bot_identity_client_id`, `bot_identity_tenant_id`, and `tags`. The three identity variables receive the pre-created user-assigned identity from `main.tf`.

### `terraform/modules/bot-service/outputs.tf`

Two outputs: `id` and `name` of the Bot Service resource. Identity outputs are not needed here since the identity is a standalone resource in `main.tf`.

### `search-setup/setup_search_index.py`

A standalone Python script that creates the complete AI Search pipeline via SDK and REST API calls. Accepts configuration via CLI arguments or environment variables. Idempotent (uses create-or-update for all resources). Creates four components:

1. **Data source** — Blob data source pointing at the `terms-and-conditions` container using a storage connection string.
2. **Index** — Schema with 7 fields including `chunk` (searchable, English analyzer), `text_vector` (1536-dim HNSW with Azure OpenAI vectorizer using `text-embedding-3-small`), and semantic config designating `chunk` as content and `title` as title field.
3. **Skillset** (via REST, preview API) — Three skills chained together: `DocumentLayoutSkill` (structure-aware PDF extraction to markdown), `SplitSkill` (2000-char pages with 500-char overlap), and `#Microsoft.Skills.Text.AzureOpenAIEmbeddingSkill` (generates vectors for each chunk using `text-embedding-3-small`). Uses managed identity for search-to-OpenAI and search-to-Document Intelligence auth. Includes index projections to map chunks into the one-to-many parent/child index structure, with mappings for `chunk`, `text_vector`, `title`, `metadata_storage_path`, and `metadata_storage_name`.
4. **Indexer** — Connects data source → skillset → index with field mappings for storage metadata. After creation, the script triggers the indexer to start processing immediately.

### `search-setup/requirements.txt`

Three dependencies for the setup script: `azure-search-documents>=11.6.0`, `azure-core>=1.29.0`, and `requests>=2.31.0` (for REST API calls to preview endpoints not yet in the SDK).

---

## Post-Implementation Audit Fixes

A workflow simulation (terraform apply → search setup → runtime) uncovered 7 issues. All have been fixed.

| # | Severity | Issue | Fix |
|---|----------|-------|-----|
| 1 | **Critical** | **Circular Terraform dependency** — `function_app` referenced `bot_service.bot_identity_*` outputs while `bot_service` referenced `function_app.hostname`. Terraform would detect a cycle and refuse to plan. | Extracted `azurerm_user_assigned_identity` out of bot-service module into a standalone resource in `main.tf`. Both modules now reference it independently. |
| 2 | **Critical** | **Wrong credential for OpenAI & Search** — A single `get_credential()` returned the bot's user-assigned identity for all calls, but RBAC roles for OpenAI (`Cognitive Services OpenAI User`) and Search (`Search Index Data Reader`) are assigned to the Function App's system-assigned identity. Would cause 403 Forbidden on every RAG call. | Split into `get_service_credential()` (returns `DefaultAzureCredential`, resolves to system-assigned identity) for OpenAI/Search and `get_bot_credential()` (returns `ManagedIdentityCredential` with bot client_id) for Bot Framework token only. |
| 3 | **Critical** | **Wrong embedding skill odata type** — `#Microsoft.Skills.Custom.AzureOpenAIEmbeddingSkill` does not exist. Indexer creation would fail. | Fixed to `#Microsoft.Skills.Text.AzureOpenAIEmbeddingSkill`. |
| 4 | **Moderate** | **Missing metadata in index projections** — `metadata_storage_path` and `metadata_storage_name` were in the index schema and `fieldMappings` but not in the projection selector's `mappings`. With `generatedKeyAsId` projections, only explicitly mapped fields are populated — these would always be empty. | Added both fields to the projection selector's `mappings` array. |
| 5 | **Minor** | **Unused import** — `asyncio` was imported but never used. | Removed. |
| 6 | **Minor** | **Stale docstring** — Setup script usage example still referenced `text-embedding-3-large`. | Updated to `text-embedding-3-small`. |
| 7 | **Minor** | **Stale variable descriptions** — OpenAI module variables and comments still said "GPT-4". | Updated to generic "chat completion model" / "chat model". |
