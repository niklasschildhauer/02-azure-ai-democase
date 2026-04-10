# Example Terraform variables file
# Copy this to terraform.tfvars and customize as needed

project_name    = "frauddetect"
location        = "germanywestcentral"
openai_location = "germanywestcentral"
search_sku      = "basic"
unique_variable_name_suffix = "nik"

tags = {
  Project     = "Insurance Fraud Detection"
  Environment = "Development"
  ManagedBy   = "Terraform"
  Workshop    = "Azure AI Demo"
  CostCenter  = "IT-Innovation"
}
