"""
Flow 2 — T&C RAG Chatbot
POST /api/messages → search T&C index → GPT response → Bot Framework reply
"""

import logging
import os
import threading
import traceback

import azure.functions as func
from azure.identity import ManagedIdentityCredential, DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery
from openai import AzureOpenAI

from shared import AZURE_OPENAI_API_VERSION, AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_ENDPOINT, get_service_credential

bp = func.Blueprint()

AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "")
AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "terms-and-conditions-index")
BOT_APP_ID = os.getenv("MicrosoftAppId", "")

SYSTEM_PROMPT = """You are an insurance terms and conditions assistant. Your role is to help insurance agents find and understand information from insurance policy terms and conditions documents.

Rules:
- ONLY answer questions using the provided context from T&C documents.
- If the context does not contain enough information to answer, say so clearly.
- Cite specific sections or clauses when possible (e.g., "According to Section 3.2...").
- Never invent, assume, or fabricate information not present in the context.
- Decline questions that are not related to insurance terms and conditions politely.
- Be concise and professional in your responses.
"""


def get_bot_credential():
    """User-assigned managed identity for Bot Framework auth; falls back to DefaultAzureCredential locally."""
    if BOT_APP_ID:
        return ManagedIdentityCredential(client_id=BOT_APP_ID)
    return DefaultAzureCredential()


def search_terms_and_conditions(query: str) -> str:
    """Hybrid search (text + vector) with semantic ranking. Returns top 5 T&C chunks as context."""
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
    """Search T&C index → build prompt → call GPT → return answer."""
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
        api_version=AZURE_OPENAI_API_VERSION,
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Context from T&C documents:\n\n{context}\n\n---\n\nQuestion: {user_message}",
        },
    ]

    response = openai_client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=messages,
        max_completion_tokens=1024,
    )

    return response.choices[0].message.content


def _send_bot_reply(service_url, conversation_id, reply):
    """Send a reply activity to the Bot Framework connector."""
    import requests

    reply_url = f"{service_url.rstrip('/')}/v3/conversations/{conversation_id}/activities"
    try:
        credential = get_bot_credential()
        token = credential.get_token("https://api.botframework.com/.default").token
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        resp = requests.post(reply_url, json=reply, headers=headers, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to send reply via Bot service: {e}")


def _process_and_reply(body, user_text):
    """Run the RAG pipeline and send the reply; executes in a background thread."""
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


@bp.route(route="messages", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
async def messages(req: func.HttpRequest) -> func.HttpResponse:
    """Bot Framework /api/messages endpoint.
    Returns 200 immediately; RAG processing runs in a background thread to stay within the 15s webhook timeout."""
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

        thread = threading.Thread(target=_process_and_reply, args=(body, user_text))
        thread.start()

        return func.HttpResponse(status_code=200)

    elif activity_type == "conversationUpdate":
        # Send welcome message to any new member (excluding the bot itself)
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

    return func.HttpResponse(status_code=200)
