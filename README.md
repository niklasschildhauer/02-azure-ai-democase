# Azure AI Services demonstration

## Which Azure services we want to demonstrate
- Form/Text Recognition with Document Intelligence
- Storage account triggers
- Azure functions (Python)
- Running Large-Language models on Azure Foundry
- Use Azure Functions as tools for an LLM
- Azure AI Search
- Azure AI Bot Service
- (Bonus) Fraud detection with embeddings models and outlier analysis

## What we will build
We will build an AI insure claim pre-classifier to assist human decision. It analyzes incoming insure claims and pre-sorts them, either for:

- accept right away
- flag for manual review
- reject right away

To increase result quality, the classifier:
- pre-fetches the insurance terms of the given contract (we currently assume there is only one contract type)

Furthermore, we will add a chatbot, which:
- Allows insurance agents to query insurance terms and conditions
- Tell insurance agents how many claims are yet to be reviewed


## Prerequisites

### GitHub Token for Bootstrap Terraform

The bootstrap Terraform automatically creates GitHub Actions variables for Azure OIDC authentication. To enable this, you need a GitHub Personal Access Token (PAT).

1. Create a PAT at https://github.com/settings/tokens with the `repo` scope
2. Provide the token to Terraform via one of these methods:
   - Set the environment variable: `export GITHUB_TOKEN=<your-token>`
   - Or pass it directly: `terraform apply -var="github_token=<your-token>"`

The following GitHub Actions variables will be created automatically:
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `STORAGE_ACCOUNT_NAME`
- `UNIQUE_SUFFIX`
