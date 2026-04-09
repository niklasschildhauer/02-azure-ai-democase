"""Shared configuration and credentials used by both flows."""

import os

from azure.identity import DefaultAzureCredential

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-16")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "")


def get_service_credential():
    """Managed identity credential; DefaultAzureCredential handles local dev automatically."""
    return DefaultAzureCredential()
