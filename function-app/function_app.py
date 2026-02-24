"""
Azure Function App - Document Intelligence Processor
Automatically processes PDF documents when uploaded to blob storage
"""

import azure.functions as func
import logging
import os
import json
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp()

# Environment variables
DOC_INTEL_ENDPOINT = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")
DOC_INTEL_KEY = os.getenv("DOCUMENT_INTELLIGENCE_KEY")
DATA_STORAGE_CONN = os.getenv("DataStorageConnection")
OUTPUT_CONTAINER = os.getenv("OUTPUT_CONTAINER_NAME", "processed-data")


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
