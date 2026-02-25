# Azure AI Services demonstration

## Which Azure services we want to demonstrate
- Form/Text Recognition with Document Intelligence
- Storage account triggers
- Azure functions (Python)
- Running Large-Language models on Azure (Cognitive Accounts, Cognitive Deployments)
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


## Architecture
