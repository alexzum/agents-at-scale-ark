# ARK Banking Demo Storyline

## **Demo Theme: "Smart Customer Service Hub for Regional Bank"**

### **Business Context**
A regional bank wants to modernize their customer service operations by deploying AI agents that can handle different types of customer inquiries efficiently. The goal is to show how ARK enables enterprise-grade AI agent management with proper DevOps practices.

---

## **Demo Architecture**

### **Namespace: `demo-bank`**
- Clean, isolated environment
- Professional Kubernetes resource management

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
