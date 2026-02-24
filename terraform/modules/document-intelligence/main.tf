# Azure AI Document Intelligence Module
# Provides OCR and form recognition capabilities

resource "azurerm_cognitive_account" "doc_intelligence" {
  name                = var.name
  resource_group_name = var.resource_group_name
  location            = var.location
  kind                = "FormRecognizer"
  sku_name            = var.sku_name

  tags = var.tags
}
