"""
Flow 1 — Insurance Claims Pipeline
PDF → Document Intelligence → processed-data → GPT verdict → model-analysis-results
"""

import json
import logging
import os

import azure.functions as func
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.storage.blob import BlobServiceClient
from openai import AzureOpenAI

from shared import AZURE_OPENAI_API_VERSION, AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_ENDPOINT, get_service_credential

bp = func.Blueprint()

DOC_INTEL_ENDPOINT = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")
DATA_STORAGE_ACCOUNT_URL = os.getenv("DATA_STORAGE_ACCOUNT_URL", "")
OUTPUT_CONTAINER = os.getenv("OUTPUT_CONTAINER_NAME", "processed-data")
MODEL_ANALYSIS_CONTAINER = os.getenv("MODEL_ANALYSIS_CONTAINER_NAME", "model-analysis-results")

with open(os.path.join(os.path.dirname(__file__), "fraud_rules.json")) as _f:
    _FRAUD_RULES = json.load(_f)


@bp.blob_trigger(
    arg_name="blob",
    path="insurance-claims/{name}",
    connection="DataStorageConnection"
)
def process_insurance_claim(blob: func.InputStream):
    """Step 1: Extract structured data from a claim PDF using Document Intelligence.
    Output written to processed-data/, which triggers analyze_with_gpt5."""
    blob_filename = blob.name.split("/", 1)[-1] if "/" in blob.name else blob.name
    logging.info(f"Processing blob: {blob_filename}, Size: {blob.length} bytes")

    try:
        doc_client = DocumentAnalysisClient(
            endpoint=DOC_INTEL_ENDPOINT,
            credential=get_service_credential()
        )

        pdf_bytes = blob.read()

        # prebuilt-document extracts text, key-value pairs, and tables
        # Switch to "prebuilt-invoice" if claims are always invoice-format PDFs
        poller = doc_client.begin_analyze_document(
            model_id="prebuilt-document",
            document=pdf_bytes
        )
        result = poller.result()

        extracted_data = {
            "source_file": blob_filename,
            "pages": len(result.pages),
            "content": result.content,
            "key_value_pairs": {},
            "tables": [],
            "fraud_indicators": []
        }

        # Key-value pairs (e.g. claimant name, dates, amounts)
        if result.key_value_pairs:
            for kv_pair in result.key_value_pairs:
                if kv_pair.key and kv_pair.value:
                    key_text = kv_pair.key.content if kv_pair.key.content else ""
                    value_text = kv_pair.value.content if kv_pair.value.content else ""
                    extracted_data["key_value_pairs"][key_text] = value_text

        # Raw table cells (preserved for audit; GPT analysis uses key_value_pairs instead)
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

        # Heuristic fraud checks loaded from fraud_rules.json — GPT incorporates these in step 2
        content_lower = result.content.lower()
        kv = extracted_data["key_value_pairs"]

        for check in _FRAUD_RULES.get("keyword_checks", []):
            if any(kw in content_lower for kw in check["keywords"]):
                extracted_data["fraud_indicators"].append(check["indicator"])

        for check in _FRAUD_RULES.get("date_comparison_checks", []):
            ef, lf = check["earlier_field"], check["later_field"]
            if ef in kv and lf in kv and kv[ef] < kv[lf]:
                extracted_data["fraud_indicators"].append(check["indicator"])

        # Write to processed-data/ — this triggers analyze_with_gpt5
        blob_service_client = BlobServiceClient(account_url=DATA_STORAGE_ACCOUNT_URL, credential=get_service_credential())
        output_blob_name = f"{os.path.splitext(blob_filename)[0]}_analyzed.json"
        output_blob_client = blob_service_client.get_blob_client(
            container=OUTPUT_CONTAINER,
            blob=output_blob_name
        )
        output_blob_client.upload_blob(
            json.dumps(extracted_data, indent=2),
            overwrite=True
        )

        logging.info(f"Extraction complete: {output_blob_name} ({len(extracted_data['fraud_indicators'])} heuristic indicators)")

    except Exception as e:
        logging.error(f"Error processing blob {blob_filename}: {str(e)}")
        raise


@bp.blob_trigger(
    arg_name="blob",
    path="processed-data/{name}",
    connection="DataStorageConnection"
)
def analyze_with_gpt5(blob: func.InputStream):
    """Step 2: Produce a GPT verdict from the Document Intelligence extraction.
    Output written to model-analysis-results/ as a clean JSON verdict."""
    blob_filename = blob.name.split("/", 1)[-1] if "/" in blob.name else blob.name
    logging.info(f"Analyzing blob: {blob_filename}")

    try:
        if not blob_filename.endswith('.json'):
            logging.info(f"Skipping non-JSON file: {blob_filename}")
            return

        document_data = json.loads(blob.read().decode('utf-8'))

        credential = get_service_credential()
        client = AzureOpenAI(
            azure_ad_token_provider=lambda: credential.get_token(
                "https://cognitiveservices.azure.com/.default"
            ).token,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )

        # Send only the fields the model needs — raw table cells are excluded
        prompt_data = {
            "key_value_pairs": document_data.get("key_value_pairs", {}),
            "content": document_data.get("content", ""),
            "existing_fraud_indicators": document_data.get("fraud_indicators", [])
        }

        prompt = f"""Analyze the following insurance claim data and return a JSON object with exactly these fields:

{{
  "summary": "<2-3 sentence summary of the claim>",
  "risk_level": "<Low | Medium | High>",
  "fraud_indicators": ["<indicator 1>", "..."],
  "recommended_next_steps": ["<step 1>", "..."]
}}

Note: existing_fraud_indicators have already been flagged by automated checks — incorporate them into your analysis.

Claim data:
{json.dumps(prompt_data, indent=2)}"""

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
            response_format={"type": "json_object"},
            max_completion_tokens=6000
        )

        gpt_analysis = response.choices[0].message.content

        logging.info(f"Response finish_reason: {response.choices[0].finish_reason}")
        if not gpt_analysis:
            raise ValueError(f"Empty response from GPT. Full response: {response.model_dump_json()}")

        verdict = json.loads(gpt_analysis)

        analysis_result = {
            "source_document": blob_filename,
            "analysis_timestamp": response.created,
            "model_used": AZURE_OPENAI_DEPLOYMENT,
            "verdict": verdict
        }

        blob_service_client = BlobServiceClient(account_url=DATA_STORAGE_ACCOUNT_URL, credential=get_service_credential())
        output_blob_name = f"{os.path.splitext(blob_filename)[0]}_gpt5_analysis.json"
        output_blob_client = blob_service_client.get_blob_client(
            container=MODEL_ANALYSIS_CONTAINER,
            blob=output_blob_name
        )
        output_blob_client.upload_blob(
            json.dumps(analysis_result, indent=2),
            overwrite=True
        )

        logging.info(f"Verdict saved: {output_blob_name} (tokens used: {response.usage.total_tokens})")

    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in blob {blob_filename}: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Error analyzing blob {blob_filename} with GPT: {str(e)}")
        raise
