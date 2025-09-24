# ARK Banking Demo Storyline

## **Demo Theme: "Smart Customer Service Hub for Regional Bank"**

### **Business Context**
A regional bank wants to modernize their customer service operations by deploying AI agents that can handle different types of customer inquiries efficiently. The goal is to show how ARK enables enterprise-grade AI agent management with proper DevOps practices.

---

## **Demo Architecture**

### **Namespace: `demo-bank`**
- Clean, isolated environment for demo
- Professional Kubernetes resource management
- Easy cleanup post-demo

### **Core Agents (3-Agent Workflow)**

#### **1. Inquiry Router Agent**
- **Purpose**: Classifies incoming customer requests
- **Classifications**: 
  - `account` - Balance, transactions, account status
  - `loan` - Loan products, rates, eligibility
  - `mixed` - Requests needing multiple agents
- **Sample Input**: "What's my account balance and what loans do you offer?"
- **Output**: Classification + routing decision

#### **2. Account Helper Agent** 
- **Purpose**: Handles account-related inquiries
- **Capabilities**:
  - Account balance (placeholder: "$2,450.67")
  - Recent transactions (placeholder: "Last payment: $150 on Dec 20")
  - Account status (placeholder: "Active, Good Standing")
- **Sample Response**: "Your current balance is $2,450.67. Your account is in good standing."

#### **3. Loan Advisor Agent**
- **Purpose**: Provides loan information and guidance
- **Capabilities**:
  - Available loan products
  - Current rates (placeholder: "Mortgage: 6.5%, Personal: 8.9%")
  - Basic eligibility requirements
- **Sample Response**: "We offer mortgages at 6.5% and personal loans at 8.9%. Would you like to schedule a consultation?"

---

## **Demo Workflow (Sequential Team Strategy)**

### **Scenario: Mixed Customer Request**
**Customer Input**: "What's my account balance and what loans do you offer?"

#### **Step 1: Classification**
- **Inquiry Router** receives request
- Classifies as: `mixed` (requires both account + loan info)
- Routes to **Customer Service Team**

#### **Step 2: Account Information** 
- **Account Helper** processes account portion
- Returns: Balance and account status
- Passes context to next agent

#### **Step 3: Loan Information**
- **Loan Advisor** processes loan inquiry
- Returns: Available products and rates
- Combines with account context

#### **Step 4: Coordinated Response**
- **Team coordination** merges responses
- Final output: Complete answer addressing both requests
- **Response**: "Your account balance is $2,450.67 and your account is in good standing. For loans, we offer mortgages at 6.5% and personal loans at 8.9%. Would you like to schedule a consultation?"

---

## **Demo Value Propositions**

### **For Banks**
- **Efficiency**: Instant responses vs. hours of wait time
- **Consistency**: Standardized, accurate information
- **Scalability**: Handle multiple customers simultaneously
- **Compliance**: Built-in audit trails and governance
- **Cost Reduction**: Reduce call center volume

### **For Technical Audience** 
- **Enterprise DevOps**: GitOps deployments, version control
- **Kubernetes-Native**: Standard K8s resource management
- **Observability**: Full request tracing and monitoring
- **API Integration**: Easy integration with existing systems
- **Multi-Agent Orchestration**: Complex workflow coordination

---

## **Demo Technical Highlights**

### **Agent Management**
- Deploy agents via YAML (GitOps-ready)
- Version control and rollbacks
- Resource isolation and scaling

### **Team Orchestration**
- Sequential workflow execution
- Context passing between agents
- Error handling and fallbacks

### **Enterprise Integration**
- REST API endpoints for all operations
- Prometheus metrics and OpenTelemetry traces
- Integration with existing systems (future: LegacyX calls)

### **Observability & Monitoring**
- Request tracing across agents
- Performance metrics and alerts
- Langfuse integration for AI-specific monitoring

---

## **Demo Duration: ~15 minutes**

### **Timeline**
- **Setup** (2 min): Deploy agents to demo-bank namespace
- **Agent Demo** (5 min): Show individual agent responses
- **Team Workflow** (5 min): Demonstrate coordinated multi-agent response
- **API Integration** (2 min): Show curl commands for external integration
- **Observability** (1 min): Quick look at metrics and tracing

### **Audience Engagement Points**
- "This customer request would normally take 5-10 minutes on a call..."
- "Notice how the agents maintain context and provide consistent responses..."
- "Your existing systems can integrate via these API endpoints..."
- "All of this is version controlled and deployed like any other service..."

---

## **Success Metrics for Demo**
- ✅ **Response Time**: Sub-second agent responses
- ✅ **Accuracy**: Relevant, contextual answers
- ✅ **Coordination**: Seamless team workflow
- ✅ **Enterprise Readiness**: Professional deployment practices
- ✅ **Integration Ready**: API endpoints working
- ✅ **Observable**: Full monitoring and tracing

This storyline balances **business relevance** for banking executives with **technical depth** for engineering teams, while keeping the complexity manageable for a live demo.
