"""
Search Index Setup Script
Creates data source, index, skillset, and indexer for the T&C RAG pipeline.
Idempotent: creates or updates all components.

Usage:
    python setup_search_index.py \
        --search-endpoint https://<name>.search.windows.net \
        --search-admin-key <key> \
        --storage-connection-string "<conn-string>" \
        --storage-container terms-and-conditions \
        --openai-endpoint https://<name>.openai.azure.com \
        --openai-embedding-deployment text-embedding-3-small \
        --ai-services-endpoint https://<name>.cognitiveservices.azure.com

    All arguments can also be set via environment variables:
        AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_ADMIN_KEY,
        AZURE_STORAGE_CONNECTION_STRING, AZURE_STORAGE_CONTAINER,
        AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        AZURE_AI_SERVICES_ENDPOINT
"""

import argparse
import json
import os
import sys

import requests
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters,
    HnswAlgorithmConfiguration,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)

# Constants
INDEX_NAME = "terms-and-conditions-index"
DATA_SOURCE_NAME = "terms-and-conditions-datasource"
SKILLSET_NAME = "terms-and-conditions-skillset"
INDEXER_NAME = "terms-and-conditions-indexer"
SEARCH_API_VERSION = "2024-11-01-preview"


def parse_args():
    parser = argparse.ArgumentParser(description="Set up Azure AI Search index for T&C RAG")
    parser.add_argument("--search-endpoint", default=os.getenv("AZURE_SEARCH_ENDPOINT"))
    parser.add_argument("--search-admin-key", default=os.getenv("AZURE_SEARCH_ADMIN_KEY"))
    parser.add_argument(
        "--storage-connection-string", default=os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    )
    parser.add_argument(
        "--storage-container", default=os.getenv("AZURE_STORAGE_CONTAINER", "terms-and-conditions")
    )
    parser.add_argument("--openai-endpoint", default=os.getenv("AZURE_OPENAI_ENDPOINT"))
    parser.add_argument(
        "--openai-embedding-deployment",
        default=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002"),
    )
    parser.add_argument(
        "--ai-services-endpoint", default=os.getenv("AZURE_AI_SERVICES_ENDPOINT")
    )
    args = parser.parse_args()

    required = [
        ("search_endpoint", args.search_endpoint),
        ("search_admin_key", args.search_admin_key),
        ("storage_connection_string", args.storage_connection_string),
        ("openai_endpoint", args.openai_endpoint),
        ("ai_services_endpoint", args.ai_services_endpoint),
    ]
    missing = [name for name, val in required if not val]
    if missing:
        parser.error(f"Missing required arguments: {', '.join(missing)}")

    return args


def rest_headers(admin_key):
    return {
        "Content-Type": "application/json",
        "api-key": admin_key,
    }


def raise_for_status(resp, context):
    """Print response body on error before raising, for easier debugging."""
    if not resp.ok:
        print(f"  ERROR {resp.status_code} on {context}:")
        print(f"  {resp.text}")
    resp.raise_for_status()


def create_or_update_data_source(args):
    """Create or update the blob data source connection."""
    print(f"Creating data source: {DATA_SOURCE_NAME}")
    url = (
        f"{args.search_endpoint}/datasources/{DATA_SOURCE_NAME}"
        f"?api-version={SEARCH_API_VERSION}"
    )
    body = {
        "name": DATA_SOURCE_NAME,
        "type": "azureblob",
        "credentials": {"connectionString": args.storage_connection_string},
        "container": {"name": args.storage_container},
    }
    resp = requests.put(url, headers=rest_headers(args.search_admin_key), json=body)
    raise_for_status(resp, "data source")
    print(f"  Data source '{DATA_SOURCE_NAME}' created/updated successfully")


def create_or_update_index(args):
    """Create or update the search index with vector and semantic config."""
    print(f"Creating index: {INDEX_NAME}")
    credential = AzureKeyCredential(args.search_admin_key)
    index_client = SearchIndexClient(endpoint=args.search_endpoint, credential=credential)

    fields = [
        SearchField(name="chunk_id", type=SearchFieldDataType.String, key=True, filterable=True, analyzer_name="keyword"),
        SimpleField(name="parent_id", type=SearchFieldDataType.String, filterable=True),
        SearchableField(
            name="title", type=SearchFieldDataType.String, filterable=True, sortable=True
        ),
        SearchableField(
            name="chunk",
            type=SearchFieldDataType.String,
            analyzer_name="en.microsoft",
        ),
        SearchField(
            name="text_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="tc-vector-profile",
        ),
        SimpleField(
            name="metadata_storage_path", type=SearchFieldDataType.String, filterable=True
        ),
        SimpleField(
            name="metadata_storage_name", type=SearchFieldDataType.String, filterable=True
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="tc-hnsw-config")],
        vectorizers=[
            AzureOpenAIVectorizer(
                vectorizer_name="tc-openai-vectorizer",
                parameters=AzureOpenAIVectorizerParameters(
                    resource_url=args.openai_endpoint,
                    deployment_name=args.openai_embedding_deployment,
                    model_name="text-embedding-ada-002",
                ),
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="tc-vector-profile",
                algorithm_configuration_name="tc-hnsw-config",
                vectorizer_name="tc-openai-vectorizer",
            )
        ],
    )

    semantic_config = SemanticConfiguration(
        name="tc-semantic-config",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="title"),
            content_fields=[SemanticField(field_name="chunk")],
        ),
    )

    semantic_search = SemanticSearch(configurations=[semantic_config])

    index = SearchIndex(
        name=INDEX_NAME,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search,
    )

    index_client.create_or_update_index(index)
    print(f"  Index '{INDEX_NAME}' created/updated successfully")


def create_or_update_skillset(args):
    """Create or update the skillset (REST API for preview features)."""
    print(f"Creating skillset: {SKILLSET_NAME}")
    url = (
        f"{args.search_endpoint}/skillsets/{SKILLSET_NAME}"
        f"?api-version={SEARCH_API_VERSION}"
    )
    body = {
        "name": SKILLSET_NAME,
        "description": "Skillset for T&C document processing: layout analysis, chunking, embedding",
        "skills": [
            {
                "@odata.type": "#Microsoft.Skills.Util.DocumentIntelligenceLayoutSkill",
                "name": "document-layout",
                "description": "Extract structured content from PDFs using Document Intelligence",
                "context": "/document",
                "outputMode": "oneToMany",
                "markdownHeaderDepth": "h3",
                "inputs": [
                    {"name": "file_data", "source": "/document/file_data"}
                ],
                "outputs": [
                    {"name": "markdown_document", "targetName": "markdown_document"}
                ],
            },
            {
                "@odata.type": "#Microsoft.Skills.Text.SplitSkill",
                "name": "text-split",
                "description": "Split markdown into chunks",
                "context": "/document/markdown_document/*",
                "textSplitMode": "pages",
                "maximumPageLength": 2000,
                "pageOverlapLength": 500,
                "inputs": [
                    {"name": "text", "source": "/document/markdown_document/*/content"}
                ],
                "outputs": [
                    {"name": "textItems", "targetName": "chunks"}
                ],
            },
            {
                "@odata.type": "#Microsoft.Skills.Text.AzureOpenAIEmbeddingSkill",
                "name": "embedding",
                "description": "Generate embeddings for each chunk",
                "context": "/document/markdown_document/*/chunks/*",
                "resourceUri": args.openai_endpoint,
                "deploymentId": args.openai_embedding_deployment,
                "modelName": "text-embedding-ada-002",
                "inputs": [
                    {"name": "text", "source": "/document/markdown_document/*/chunks/*"}
                ],
                "outputs": [
                    {"name": "embedding", "targetName": "text_vector"}
                ],
            },
        ],
        "cognitiveServices": {
            "@odata.type": "#Microsoft.Azure.Search.AIServicesByIdentity",
            "description": "AI Services billing via managed identity",
            "subdomainUrl": args.ai_services_endpoint,
        },
        "indexProjections": {
            "selectors": [
                {
                    "targetIndexName": INDEX_NAME,
                    "parentKeyFieldName": "parent_id",
                    "sourceContext": "/document/markdown_document/*/chunks/*",
                    "mappings": [
                        {"name": "chunk", "source": "/document/markdown_document/*/chunks/*"},
                        {"name": "text_vector", "source": "/document/markdown_document/*/chunks/*/text_vector"},
                        {"name": "title", "source": "/document/metadata_storage_name"},
                        {"name": "metadata_storage_path", "source": "/document/metadata_storage_path"},
                        {"name": "metadata_storage_name", "source": "/document/metadata_storage_name"},
                    ],
                }
            ],
            "parameters": {"projectionMode": "skipIndexingParentDocuments"},
        },
    }
    resp = requests.put(url, headers=rest_headers(args.search_admin_key), json=body)
    raise_for_status(resp, "skillset")
    print(f"  Skillset '{SKILLSET_NAME}' created/updated successfully")


def create_or_update_indexer(args):
    """Create or update the indexer that connects data source -> skillset -> index."""
    print(f"Creating indexer: {INDEXER_NAME}")
    url = (
        f"{args.search_endpoint}/indexers/{INDEXER_NAME}"
        f"?api-version={SEARCH_API_VERSION}"
    )
    body = {
        "name": INDEXER_NAME,
        "dataSourceName": DATA_SOURCE_NAME,
        "targetIndexName": INDEX_NAME,
        "skillsetName": SKILLSET_NAME,
        "fieldMappings": [
            {
                "sourceFieldName": "metadata_storage_path",
                "targetFieldName": "metadata_storage_path",
            },
            {
                "sourceFieldName": "metadata_storage_name",
                "targetFieldName": "metadata_storage_name",
            },
        ],
        "outputFieldMappings": [],
        "parameters": {
            "configuration": {
                "dataToExtract": "contentAndMetadata",
                "parsingMode": "default",
                "allowSkillsetToReadFileData": True,
            }
        },
    }
    resp = requests.put(url, headers=rest_headers(args.search_admin_key), json=body)
    raise_for_status(resp, "indexer")
    print(f"  Indexer '{INDEXER_NAME}' created/updated successfully")


def run_indexer(args):
    """Trigger the indexer to start processing."""
    print(f"Running indexer: {INDEXER_NAME}")
    url = (
        f"{args.search_endpoint}/indexers/{INDEXER_NAME}/run"
        f"?api-version={SEARCH_API_VERSION}"
    )
    resp = requests.post(url, headers=rest_headers(args.search_admin_key))
    if resp.status_code == 409:
        print(f"  Indexer '{INDEXER_NAME}' is already running — skipping explicit run")
        return
    raise_for_status(resp, "run indexer")
    print(f"  Indexer '{INDEXER_NAME}' triggered successfully")


def main():
    args = parse_args()

    print("=" * 60)
    print("Azure AI Search - T&C Index Setup")
    print("=" * 60)
    print(f"Search endpoint: {args.search_endpoint}")
    print(f"OpenAI endpoint: {args.openai_endpoint}")
    print(f"Container:       {args.storage_container}")
    print()

    create_or_update_data_source(args)
    create_or_update_index(args)
    create_or_update_skillset(args)
    create_or_update_indexer(args)
    run_indexer(args)

    print()
    print("=" * 60)
    print("Setup complete! The indexer is now running.")
    print(f"Check status: az search indexer status --name {INDEXER_NAME}")
    print("=" * 60)


if __name__ == "__main__":
    main()
