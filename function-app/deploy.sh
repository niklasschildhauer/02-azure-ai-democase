#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Azure Function Deployment Script ===${NC}"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}Error: Azure CLI is not installed${NC}"
    exit 1
fi

# Check if Functions Core Tools is installed
if ! command -v func &> /dev/null; then
    echo -e "${RED}Error: Azure Functions Core Tools not installed${NC}"
    echo "Install with: brew install azure-functions-core-tools@4"
    exit 1
fi

# Get project name from terraform (or use default)
PREFIX="<changeme>"
PROJECT_NAME=${1:-"frauddetect"}
FUNCTION_APP_NAME="${PREFIX}-func-${PROJECT_NAME}"
RESOURCE_GROUP="${PREFIX}-rg-${PROJECT_NAME}"

echo -e "${YELLOW}Function App: ${FUNCTION_APP_NAME}${NC}"
echo -e "${YELLOW}Resource Group: ${RESOURCE_GROUP}${NC}"

# Check if logged in to Azure
echo -e "\n${GREEN}Checking Azure login...${NC}"
if ! az account show &> /dev/null; then
    echo -e "${RED}Not logged in to Azure${NC}"
    az login
fi

# Check if resource group exists
echo -e "\n${GREEN}Checking if resource group exists...${NC}"
if ! az group show --name "${RESOURCE_GROUP}" &> /dev/null; then
    echo -e "${RED}Error: Resource group '${RESOURCE_GROUP}' not found${NC}"
    echo -e "${YELLOW}Run 'terraform apply' first to create infrastructure${NC}"
    exit 1
fi

# Check if function app exists
echo -e "\n${GREEN}Checking if function app exists...${NC}"
if ! az functionapp show --name "${FUNCTION_APP_NAME}" --resource-group "${RESOURCE_GROUP}" &> /dev/null; then
    echo -e "${RED}Error: Function app '${FUNCTION_APP_NAME}' not found${NC}"
    echo -e "${YELLOW}Run 'terraform apply' first to create infrastructure${NC}"
    exit 1
fi

# Build and publish function
echo -e "\n${GREEN}Publishing function app...${NC}"
func azure functionapp publish "${FUNCTION_APP_NAME}" --python

echo -e "\n${GREEN}=== Deployment Complete ===${NC}"
echo -e "${YELLOW}Function App URL: https://${FUNCTION_APP_NAME}.azurewebsites.net${NC}"
echo -e "${YELLOW}Stream logs with: func azure functionapp logstream ${FUNCTION_APP_NAME}${NC}"
