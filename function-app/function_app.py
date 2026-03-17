"""
Azure Function App - Document Intelligence Processor + T&C RAG Chatbot
- Blob trigger: processes insurance claim PDFs via Document Intelligence
- HTTP trigger: /api/messages endpoint for Bot Framework (T&C RAG chatbot)
"""

import json
import logging
import os
import threading
import traceback

import azure.functions as func
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery
from azure.storage.blob import BlobServiceClient
from openai import AzureOpenAI

app = func.FunctionApp()

# ──────────────────────────────────────────────
# Environment variables - Document Processing
# ──────────────────────────────────────────────
DOC_INTEL_ENDPOINT = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")
DOC_INTEL_KEY = os.getenv("DOCUMENT_INTELLIGENCE_KEY")
DATA_STORAGE_CONN = os.getenv("DataStorageConnection")
OUTPUT_CONTAINER = os.getenv("OUTPUT_CONTAINER_NAME", "processed-data")


# ──────────────────────────────────────────────
# Environment variables - RAG Chatbot
# ──────────────────────────────────────────────
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-16")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "")
AZURE_OPENAI_CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "")
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "")
AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "terms-and-conditions-index")
BOT_APP_ID = os.getenv("MicrosoftAppId", "")
BOT_TENANT_ID = os.getenv("MicrosoftAppTenantId", "")
MODEL_ANALYSIS_CONTAINER = os.getenv("MODEL_ANALYSIS_CONTAINER_NAME", "model-analysis-results")


SYSTEM_PROMPT = """You are an insurance terms and conditions assistant. Your role is to help insurance agents find and understand information from insurance policy terms and conditions documents.

Rules:
- ONLY answer questions using the provided context from T&C documents.
- If the context does not contain enough information to answer, say so clearly.
- Cite specific sections or clauses when possible (e.g., "According to Section 3.2...").
- Never invent, assume, or fabricate information not present in the context.
- Decline questions that are not related to insurance terms and conditions politely.
- Be concise and professional in your responses.
"""


@app.blob_trigger(
    arg_name="blob",
    path="insurance-claims/{name}",
    connection="DataStorageConnection"
)
def process_insurance_claim(blob: func.InputStream):
    """
    Triggered when a PDF is uploaded to the 'insurance-claims' container.
    Analyzes the document using Document Intelligence and stores results.
    """
    logging.info(f"Processing blob: {blob.name}, Size: {blob.length} bytes")

    try:
        # Initialize Document Intelligence client
        doc_client = DocumentAnalysisClient(
            endpoint=DOC_INTEL_ENDPOINT,
            credential=AzureKeyCredential(DOC_INTEL_KEY)
        )

        # Read blob content
        pdf_bytes = blob.read()
        logging.info(f"Read {len(pdf_bytes)} bytes from blob {blob.name}")

        # Analyze document using prebuilt-document model
        # For invoices, you can use "prebuilt-invoice" model
        poller = doc_client.begin_analyze_document(
            model_id="prebuilt-document",  # or "prebuilt-invoice" for invoices
            document=pdf_bytes
        )
        result = poller.result()

        # Extract structured data
        extracted_data = {
            "source_file": blob.name,
            "pages": len(result.pages),
            "content": result.content,
            "key_value_pairs": {},
            "tables": [],
            "fraud_indicators": []
        }

        # Extract key-value pairs
        if result.key_value_pairs:
            for kv_pair in result.key_value_pairs:
                if kv_pair.key and kv_pair.value:
                    key_text = kv_pair.key.content if kv_pair.key.content else ""
                    value_text = kv_pair.value.content if kv_pair.value.content else ""
                    extracted_data["key_value_pairs"][key_text] = value_text

        # Extract tables
        if result.tables:
            for table_idx, table in enumerate(result.tables):
                table_data = {
                    "table_id": table_idx,
                    "row_count": table.row_count,
                    "column_count": table.column_count,
                    "cells": []
                }
                for cell in table.cells:
                    table_data["cells"].append({
                        "row_index": cell.row_index,
                        "column_index": cell.column_index,
                        "content": cell.content
                    })
                extracted_data["tables"].append(table_data)

        # Simple fraud detection logic (example)
        content_lower = result.content.lower()
        if "urgent" in content_lower or "immediate payment" in content_lower:
            extracted_data["fraud_indicators"].append("Urgent language detected")

        # Check for date inconsistencies (basic example)
        if "invoice date" in extracted_data["key_value_pairs"] and "incident date" in extracted_data["key_value_pairs"]:
            invoice_date = extracted_data["key_value_pairs"]["invoice date"]
            incident_date = extracted_data["key_value_pairs"]["incident date"]
            if invoice_date < incident_date:
                extracted_data["fraud_indicators"].append("Invoice date before incident date")

        # Store results in output container
        blob_service_client = BlobServiceClient.from_connection_string(DATA_STORAGE_CONN)
        output_blob_name = f"{os.path.splitext(blob.name)[0]}_analyzed.json"
        output_blob_client = blob_service_client.get_blob_client(
            container=OUTPUT_CONTAINER,
            blob=output_blob_name
        )

        # Upload analyzed data as JSON
        output_blob_client.upload_blob(
            json.dumps(extracted_data, indent=2),
            overwrite=True
        )

        logging.info(f"Successfully processed {blob.name}, results saved to {output_blob_name}")
        logging.info(f"Fraud indicators found: {len(extracted_data['fraud_indicators'])}")

    except Exception as e:
        logging.error(f"Error processing blob {blob.name}: {str(e)}")
        raise


@app.blob_trigger(
    arg_name="blob",
    path="processed-data/{name}",
    connection="DataStorageConnection"
)
def analyze_with_gpt5(blob: func.InputStream):
    """
    Triggered when a JSON document is uploaded to the 'processed-data' container.
    Sends the JSON to GPT-5-mini for analysis and stores the response.
    """
    logging.info(f"GPT-5 Analysis - Processing blob: {blob.name}, Size: {blob.length} bytes")
    logging.info(f"Environment - Deployment: {AZURE_OPENAI_DEPLOYMENT}, Endpoint: {AZURE_OPENAI_ENDPOINT}")

    try:
        # Only process JSON files
        if not blob.name.endswith('.json'):
            logging.info(f"Skipping non-JSON file: {blob.name}")
            return

        # Read blob content
        json_content = blob.read().decode('utf-8')
        document_data = json.loads(json_content)

        logging.info(f"Read JSON document: {blob.name}")

        # Initialize Azure OpenAI client
        client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )

        # Construct prompt for GPT-5
        prompt = f"""You are an insurance claims analyst. Analyze the following document data and provide:
1. A summary of the claim
2. Any potential fraud indicators
3. Recommended next steps for claim processing
4. Risk assessment (Low/Medium/High)

Document Data:
{json.dumps(document_data, indent=2)}

Provide your analysis in a structured format."""

        # Call GPT-5-mini
        logging.info(f"Calling Azure OpenAI deployment: {AZURE_OPENAI_DEPLOYMENT}")
        logging.info(f"Using endpoint: {AZURE_OPENAI_ENDPOINT}")
        logging.info(f"Using API version: {AZURE_OPENAI_API_VERSION}")

        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert insurance claims analyst with deep knowledge of fraud detection and risk assessment."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=1,  # Lower temperature for more consistent analysis
            max_completion_tokens=6000  # Increased to accommodate reasoning model (1500 for reasoning + 4500 for response)
        )

        # Extract analysis from response
        gpt_analysis = response.choices[0].message.content

        # Debug logging
        logging.info(f"Response finish_reason: {response.choices[0].finish_reason}")
        logging.info(f"Response content length: {len(gpt_analysis) if gpt_analysis else 0}")
        if not gpt_analysis:
            logging.warning(f"Empty response from GPT! Full response: {response}")
            logging.warning(f"Response model dump: {response.model_dump_json()}")

        # Build result object
        analysis_result = {
            "source_document": blob.name,
            "analysis_timestamp": response.created,
            "model_used": AZURE_OPENAI_DEPLOYMENT,
            "original_data": document_data,
            "gpt5_analysis": gpt_analysis,
            "token_usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }

        # Store results in model-analysis-results container
        blob_service_client = BlobServiceClient.from_connection_string(DATA_STORAGE_CONN)
        output_blob_name = f"{os.path.splitext(blob.name)[0]}_gpt5_analysis.json"
        output_blob_client = blob_service_client.get_blob_client(
            container=MODEL_ANALYSIS_CONTAINER,
            blob=output_blob_name
        )

        # Upload analysis result as JSON
        output_blob_client.upload_blob(
            json.dumps(analysis_result, indent=2),
            overwrite=True
        )

        logging.info(f"Successfully analyzed {blob.name} with GPT-5")
        logging.info(f"Results saved to {output_blob_name}")
        logging.info(f"Tokens used: {response.usage.total_tokens}")

    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in blob {blob.name}: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Error analyzing blob {blob.name} with GPT-5: {str(e)}")
        raise
# ══════════════════════════════════════════════════════════════
# T&C RAG Chatbot - Bot Framework /api/messages endpoint
# ══════════════════════════════════════════════════════════════


def get_service_credential():
    """Get credential for accessing Azure services (OpenAI, Search).
    Uses the Function App's system-assigned managed identity in Azure,
    or DefaultAzureCredential for local development."""
    return DefaultAzureCredential()


def get_bot_credential():
    """Get credential for Bot Framework authentication.
    Uses the bot's user-assigned managed identity in Azure,
    or DefaultAzureCredential for local development."""
    if BOT_APP_ID:
        return ManagedIdentityCredential(client_id=BOT_APP_ID)
    return DefaultAzureCredential()


def search_terms_and_conditions(query: str) -> str:
    """
    Perform hybrid search (text + vector) with semantic ranking against the
    T&C search index. Returns top 5 chunks formatted as context.
    """
    credential = get_service_credential()
    search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=AZURE_SEARCH_INDEX_NAME,
        credential=credential,
    )

    vector_query = VectorizableTextQuery(
        text=query,
        k_nearest_neighbors=5,
        fields="text_vector",
    )

    results = search_client.search(
        search_text=query,
        vector_queries=[vector_query],
        query_type="semantic",
        semantic_configuration_name="tc-semantic-config",
        top=5,
        select=["chunk", "title"],
    )

    context_parts = []
    for i, result in enumerate(results, 1):
        title = result.get("title", "Unknown")
        chunk = result.get("chunk", "")
        context_parts.append(f"[Source {i}: {title}]\n{chunk}")

    return "\n\n---\n\n".join(context_parts) if context_parts else ""


def get_rag_response(user_message: str) -> str:
    """Orchestrate RAG: search T&C index -> build prompt -> call OpenAI."""
    context = search_terms_and_conditions(user_message)

    if not context:
        return (
            "I couldn't find any relevant information in the terms and conditions documents. "
            "Please make sure the T&C documents have been indexed, or try rephrasing your question."
        )

    credential = get_service_credential()
    openai_client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        azure_ad_token_provider=lambda: credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        ).token,
        api_version="2024-12-01-preview",
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Context from T&C documents:\n\n{context}\n\n---\n\nQuestion: {user_message}",
        },
    ]

    response = openai_client.chat.completions.create(
        model=AZURE_OPENAI_CHAT_DEPLOYMENT,
        messages=messages,
        max_completion_tokens=1024,
    )

    return response.choices[0].message.content


def _send_bot_reply(service_url, conversation_id, reply):
    """Send a reply activity to the Bot Framework connector."""
    import requests

    reply_url = (
        f"{service_url.rstrip('/')}/v3/conversations/{conversation_id}/activities"
    )
    try:
        credential = get_bot_credential()
        token = credential.get_token(
            "https://api.botframework.com/.default"
        ).token
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        resp = requests.post(reply_url, json=reply, headers=headers, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to send reply via Bot service: {e}")


def _process_and_reply(body, user_text):
    """Process RAG query and send reply via Bot Framework (runs in background thread)."""
    try:
        answer = get_rag_response(user_text)
    except Exception:
        logging.error(f"RAG pipeline error: {traceback.format_exc()}")
        answer = "I'm sorry, I encountered an error processing your question. Please try again."

    reply = {
        "type": "message",
        "from": body.get("recipient", {}),
        "recipient": body.get("from", {}),
        "conversation": body.get("conversation", {}),
        "text": answer,
        "replyToId": body.get("id"),
    }

    service_url = body.get("serviceUrl", "")
    conversation_id = body.get("conversation", {}).get("id", "")
    if service_url and conversation_id:
        _send_bot_reply(service_url, conversation_id, reply)


@app.route(route="messages", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
async def messages(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP-triggered endpoint for Bot Framework messages.
    Handles the Activity protocol for Web Chat and other Bot channels.
    Returns 200 immediately to avoid Bot Framework's 15s webhook timeout.
    RAG processing and reply are handled in a background thread.
    """
    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse("Invalid JSON", status_code=400)

    activity_type = body.get("type", "")

    if activity_type == "message":
        user_text = body.get("text", "").strip()
        if not user_text:
            return func.HttpResponse(status_code=200)

        logging.info(f"Received message: {user_text[:100]}")

        # Process in background thread to return 200 within Bot Framework's 15s timeout
        thread = threading.Thread(
            target=_process_and_reply,
            args=(body, user_text),
        )
        thread.start()

        return func.HttpResponse(status_code=200)

    elif activity_type == "conversationUpdate":
        members_added = body.get("membersAdded", [])
        bot_id = body.get("recipient", {}).get("id", "")
        service_url = body.get("serviceUrl", "")
        conversation_id = body.get("conversation", {}).get("id", "")
        for member in members_added:
            if member.get("id") != bot_id:
                welcome = {
                    "type": "message",
                    "from": body.get("recipient", {}),
                    "recipient": member,
                    "conversation": body.get("conversation", {}),
                    "text": (
                        "Hello! I'm the Terms & Conditions Assistant. "
                        "Ask me any question about your insurance policy terms and conditions."
                    ),
                }
                if service_url and conversation_id:
                    _send_bot_reply(service_url, conversation_id, welcome)

        return func.HttpResponse(status_code=200)

    # For other activity types, just acknowledge
    return func.HttpResponse(status_code=200)
