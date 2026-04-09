"""
Azure Function App — Insurance Claims Pipeline + T&C RAG Chatbot

Flow 1 (blob-triggered, chained):
  insurance-claims/       → process_insurance_claim  (Document Intelligence extraction)
  processed-data/         → analyze_with_gpt5        (GPT verdict)
  model-analysis-results/ ← final verdict JSON

Flow 2 (HTTP):
  POST /api/messages → messages (Bot Framework T&C chatbot)
"""

import azure.functions as func

from claims_pipeline import bp as claims_bp
from rag_chatbot import bp as chatbot_bp

app = func.FunctionApp()
app.register_functions(claims_bp)
app.register_functions(chatbot_bp)
