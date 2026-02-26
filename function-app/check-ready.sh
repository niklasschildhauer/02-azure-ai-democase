#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PREFIX=${1:-"dmo"}
PROJECT_NAME=${1:-"frauddetect"}
FUNCTION_APP_NAME="${PREFIX}-func-${PROJECT_NAME}"
RESOURCE_GROUP="${PREFIX}-rg-${PROJECT_NAME}"
STORAGE_ACCOUNT="${PREFIX}${PROJECT_NAME}"
DOC_INTEL_NAME="${PREFIX}-doc-intel-${PROJECT_NAME}"

echo "=== Pre-Deployment Verification ==="
echo ""

CHECKS_PASSED=0
CHECKS_FAILED=0

# Check 1: Azure CLI
echo -n "Checking Azure CLI... "
if command -v az &> /dev/null; then
    echo -e "${GREEN}✓${NC}"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} Not installed"
    ((CHECKS_FAILED++))
fi

# Check 2: Functions Core Tools
echo -n "Checking Azure Functions Core Tools... "
if command -v func &> /dev/null; then
    VERSION=$(func --version)
    if [[ $VERSION == 4.* ]]; then
        echo -e "${GREEN}✓${NC} (v${VERSION})"
        ((CHECKS_PASSED++))
    else
        echo -e "${YELLOW}⚠${NC} Version ${VERSION} (recommend v4.x)"
        ((CHECKS_PASSED++))
    fi
else
    echo -e "${RED}✗${NC} Not installed"
    ((CHECKS_FAILED++))
fi

# Check 3: Azure login
echo -n "Checking Azure login... "
if az account show &> /dev/null; then
    ACCOUNT=$(az account show --query name -o tsv)
    echo -e "${GREEN}✓${NC} Logged in (${ACCOUNT})"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} Not logged in"
    echo "  Run: az login"
    ((CHECKS_FAILED++))
fi

# Check 4: Resource Group exists
echo -n "Checking Resource Group... "
if az group show --name "${RESOURCE_GROUP}" &> /dev/null; then
    echo -e "${GREEN}✓${NC} ${RESOURCE_GROUP} exists"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} ${RESOURCE_GROUP} not found"
    echo "  Run: cd ../terraform && terraform apply"
    ((CHECKS_FAILED++))
fi

# Check 5: Function App exists
echo -n "Checking Function App... "
if az functionapp show --name "${FUNCTION_APP_NAME}" --resource-group "${RESOURCE_GROUP}" &> /dev/null; then
    STATE=$(az functionapp show --name "${FUNCTION_APP_NAME}" --resource-group "${RESOURCE_GROUP}" --query state -o tsv)
    echo -e "${GREEN}✓${NC} ${FUNCTION_APP_NAME} exists (${STATE})"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} ${FUNCTION_APP_NAME} not found"
    echo "  Run: cd ../terraform && terraform apply"
    ((CHECKS_FAILED++))
fi

# Check 6: Storage Account exists
echo -n "Checking Storage Account... "
if az storage account show --name "${STORAGE_ACCOUNT}" --resource-group "${RESOURCE_GROUP}" &> /dev/null; then
    echo -e "${GREEN}✓${NC} ${STORAGE_ACCOUNT} exists"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} ${STORAGE_ACCOUNT} not found"
    echo "  Run: cd ../terraform && terraform apply"
    ((CHECKS_FAILED++))
fi

# Check 7: Document Intelligence exists
echo -n "Checking Document Intelligence... "
if az cognitiveservices account show --name "${DOC_INTEL_NAME}" --resource-group "${RESOURCE_GROUP}" &> /dev/null; then
    echo -e "${GREEN}✓${NC} ${DOC_INTEL_NAME} exists"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} ${DOC_INTEL_NAME} not found"
    echo "  Run: cd ../terraform && terraform apply"
    ((CHECKS_FAILED++))
fi

# Check 8: Function code files exist
echo -n "Checking function code files... "
if [[ -f "function_app.py" ]] && [[ -f "requirements.txt" ]] && [[ -f "host.json" ]]; then
    echo -e "${GREEN}✓${NC} All required files present"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} Missing files"
    [[ ! -f "function_app.py" ]] && echo "  Missing: function_app.py"
    [[ ! -f "requirements.txt" ]] && echo "  Missing: requirements.txt"
    [[ ! -f "host.json" ]] && echo "  Missing: host.json"
    ((CHECKS_FAILED++))
fi

# Check 9: In correct directory
echo -n "Checking current directory... "
if [[ $(basename $(pwd)) == "function-app" ]]; then
    echo -e "${GREEN}✓${NC} In function-app directory"
    ((CHECKS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC} Not in function-app directory"
    echo "  Current: $(pwd)"
    echo "  Run: cd function-app"
    ((CHECKS_FAILED++))
fi

echo ""
echo "=== Summary ==="
echo -e "Passed: ${GREEN}${CHECKS_PASSED}${NC}"
echo -e "Failed: ${RED}${CHECKS_FAILED}${NC}"

if [ $CHECKS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo "Ready to deploy with: ./deploy.sh"
    exit 0
else
    echo ""
    echo -e "${RED}✗ Some checks failed${NC}"
    echo "Fix the issues above before deploying"
    exit 1
fi
