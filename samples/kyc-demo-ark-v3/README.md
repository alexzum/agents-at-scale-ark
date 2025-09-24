# KYC Risk Assessment Demo - ARK v3 (RAG-Enhanced)

This demo showcases a RAG-enhanced KYC (Know Your Customer) risk assessment workflow using FAISS vector search for intelligent customer data retrieval.

## Key Innovation: RAG-Enhanced Risk Assessment

**Version 3 introduces RAG (Retrieval-Augmented Generation)** to the risk assessment process:

- **Smart Data Retrieval**: Customer profile information is stored in FAISS vector database for semantic search
- **Context-Aware Analysis**: Risk officer retrieves only relevant customer data based on query context
- **Reduced Prompt Size**: Agent prompts focus on analysis logic rather than containing large data sets
- **Scalable Architecture**: Can handle large customer databases without prompt length limitations

## Workflow Overview

The RAG-enhanced KYC risk assessment workflow consists of specialized agents:

1. **Planner Agent** (`planner-agent-kyc-v2`)
   - Creates mission plans and coordinates the workflow
   - Reviews available data and defines actionable steps
   - Ensures proper coordination between agents

2. **File Manager Agent** (`file-manager-kyc-v2`)
   - Reads KYC profile data from `/data/kyc_profile.json`
   - Saves final risk assessment documents
   - Manages file operations and provides status updates

3. **RAG-Enhanced Risk Officer Agent** (`risk-officer-rag-kyc-v3`) - **NEW**
   - Uses LangChain executor with FAISS vector store
   - Retrieves relevant customer profile information semantically
   - Analyzes customer data retrieved from vector database
   - Conducts comprehensive risk assessments
   - Generates structured reports covering financial, regulatory, and operational risks

4. **Critic Agent** (`critic-kyc`)
   - Validates output completeness and accuracy
   - Provides feedback for improvement
   - Ensures regulatory compliance and quality standards

## Team Configuration

- **Strategy**: Sequential execution
- **Max Turns**: 4 (one per agent)
- **Flow**: Planner → File Manager → Risk Officer → Critic

## Prerequisites

1. ARK controller running in cluster
2. MCP filesystem server deployed and accessible
3. KYC profile data uploaded to `/data/kyc_profile.json`

## Usage

### Deploy the workflow:
```bash
kubectl apply -k samples/kyc-demo-ark/
```

### Execute KYC assessment:
```bash
kubectl apply -f samples/kyc-demo-ark/kyc-assessment-query-with-data.yaml
```

### Monitor progress:
```bash
kubectl get queries kyc-assessment-query-with-data -w
```

### View results:
```bash
# Get query results
kubectl get queries kyc-assessment-query-with-data -o yaml

# View the risk assessment memo
kubectl get queries kyc-assessment-query-with-data -o jsonpath='{.status.responses[0].content}'

# Access generated documents via file browser
kubectl port-forward svc/mcp-filesys-filebrowser 8080:8080
# Open http://localhost:8080
```

## Expected Output

The workflow will generate a comprehensive risk assessment document including:
- Executive summary
- Customer profile analysis
- Financial, regulatory, and operational risk assessments
- Risk rating with justification
- Required documentation checklist
- Recommendations and approval status

## Customization

### Modify KYC Profile Path
Edit the file-manager agent prompt to change the input file location:
```yaml
# In agents/file-manager-agent.yaml
prompt: |
  The KYC profile is located at: /data/your_custom_profile.json
```

### Adjust Risk Assessment Criteria
Modify the risk-officer agent prompt to include custom risk factors or assessment criteria.

### Change Team Strategy
Edit `teams/kyc-risk-assessment-team.yaml` to use different execution strategies (parallel, round-robin, etc.).

## Cleanup

```bash
kubectl delete -k samples/kyc-demo-ark/
```