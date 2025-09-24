# ARK API Testing - UAT Explanation

This document explains what "Use ARK API endpoints to run UAT tests" means and provides practical examples for testing ARK agents and teams via REST APIs.

---

## **What is UAT Testing in ARK Context?**

**UAT (User Acceptance Testing)** for ARK means verifying that:
- ✅ **Agents respond correctly** to various inputs
- ✅ **Teams coordinate properly** in workflows  
- ✅ **API endpoints work** for external integration
- ✅ **Response times are acceptable** for production use
- ✅ **Error handling works** for edge cases

This is **functional testing**, not automated unit testing or performance testing.

---

## **ARK API Endpoints Overview**

### **Core API Structure**
```
http://localhost:8000/v1/namespaces/{namespace}/
├── agents/
│   ├── {agent-name}/query          # Query individual agent
│   ├── {agent-name}                # Get agent details
│   └── list                        # List all agents
├── teams/
│   ├── {team-name}/query           # Query team workflow
│   ├── {team-name}                 # Get team details
│   └── list                        # List all teams
├── queries/
│   ├── {query-id}                  # Get query details
│   └── list                        # List query history
└── models/
    └── list                        # List available models
```

---

## **UAT Test Categories**

### **1. Agent Functionality Tests**

#### **Basic Agent Response**
```bash
# Test: Can agent respond to simple queries?
curl -s -X POST "http://localhost:8000/v1/namespaces/demo-bank/queries" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "uat-basic-test",
    "input": "What is my account balance?",
    "targets": [
      {
        "type": "agent",
        "name": "account-helper"
      }
    ]
  }' | jq '.name'

# Wait for completion and get result
sleep 3
curl -s "http://localhost:8000/v1/namespaces/demo-bank/queries/uat-basic-test" | jq '.status.responses[0].content'

# Expected: Valid JSON response with account information
# Verify: Response time < 2 seconds, contains balance info
```

#### **Agent Input Validation**
```bash
# Test: How does agent handle empty input?
curl -s -X POST "http://localhost:8000/v1/namespaces/demo-bank/queries" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "uat-empty-input",
    "input": "",
    "targets": [{ "type": "agent", "name": "account-helper" }]
  }' && sleep 3 && curl -s "http://localhost:8000/v1/namespaces/demo-bank/queries/uat-empty-input" | jq '.status'

# Test: How does agent handle very long input?
curl -s -X POST "http://localhost:8000/v1/namespaces/demo-bank/queries" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "uat-long-input",
    "input": "'"$(python -c 'print("test " * 1000)')"'",
    "targets": [{ "type": "agent", "name": "account-helper" }]
  }' && sleep 3 && curl -s "http://localhost:8000/v1/namespaces/demo-bank/queries/uat-long-input" | jq '.status'

# Expected: Graceful error handling or appropriate truncation
```

#### **Agent Classification Accuracy**
```bash
# Test: Router agent classification
curl -s -X POST "http://localhost:8000/v1/namespaces/demo-bank/queries" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "uat-classification",
    "input": "I need my account balance",
    "targets": [{ "type": "agent", "name": "inquiry-router" }]
  }' && sleep 3 && curl -s "http://localhost:8000/v1/namespaces/demo-bank/queries/uat-classification" | jq '.status.responses[0].content'

# Expected: Should classify as "account" type

# Test second classification
curl -s -X POST "http://localhost:8000/v1/namespaces/demo-bank/queries" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "uat-classification-2",
    "input": "What loans do you offer?",
    "targets": [{ "type": "agent", "name": "inquiry-router" }]
  }' && sleep 3 && curl -s "http://localhost:8000/v1/namespaces/demo-bank/queries/uat-classification-2" | jq '.status.responses[0].content'

# Expected: Should classify as "loan" type
```

### **2. Team Workflow Tests**

#### **Sequential Team Execution**
```bash
# Test: Team handles mixed requests properly
curl -s -X POST "http://localhost:8000/v1/namespaces/demo-bank/queries" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "uat-team-mixed",
    "input": "I need my balance and loan information",
    "targets": [{ "type": "team", "name": "customer-service-team" }]
  }' && sleep 8 && curl -s "http://localhost:8000/v1/namespaces/demo-bank/queries/uat-team-mixed" | jq '.status.responses[0].content'

# Expected: Response contains both account and loan information
# Verify: Shows evidence of multiple agent coordination
```

#### **Team Context Passing**
```bash
# Test: Does team maintain context across agents?
curl -s -X POST "http://localhost:8000/v1/namespaces/demo-bank/queries" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "uat-team-context",
    "input": "My account number is 12345. What is my balance and what loans am I eligible for?",
    "targets": [{ "type": "team", "name": "customer-service-team" }]
  }' && sleep 8 && curl -s "http://localhost:8000/v1/namespaces/demo-bank/queries/uat-team-context" | jq '.status.responses[0].content'

# Expected: Loan recommendations should consider account info
```

### **3. System Integration Tests**

#### **API Status and Health**
```bash
# Test: Are all agents available?
curl -s "http://localhost:8000/v1/namespaces/demo-bank/agents" | jq '.items[] | {name: .name, available: .available}'

# Expected: All agents show available: "True"

# Test: System health check
curl "http://localhost:8000/health"

# Expected: 200 OK response
```

#### **Query History and Tracking**
```bash
# Test: Query history is recorded
curl "http://localhost:8000/v1/namespaces/demo-bank/queries" | jq '.items[0:5] | .[] | {id: .metadata.name, input: .spec.input, status: .status.phase}'

# Expected: Recent queries are listed with proper status
```

### **4. Error Handling Tests**

#### **Invalid Agent Names**
```bash
# Test: Non-existent agent
curl -s -X POST "http://localhost:8000/v1/namespaces/demo-bank/queries" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "uat-error-test",
    "input": "test",
    "targets": [{ "type": "agent", "name": "non-existent-agent" }]
  }' | jq '.'

# Expected: Error response with clear message about missing agent
```

#### **Malformed Requests**
```bash
# Test: Invalid JSON
curl -s -X POST "http://localhost:8000/v1/namespaces/demo-bank/queries" \
  -H "Content-Type: application/json" \
  -d '{"invalid_json": }' | jq '.'

# Expected: 400 Bad Request with JSON parsing error

# Test: Missing required fields
curl -s -X POST "http://localhost:8000/v1/namespaces/demo-bank/queries" \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.'

# Expected: 400 Bad Request indicating missing "input" field
```

---

## **UAT Test Scripts**

### **Complete Banking Demo UAT Suite**
```bash
#!/bin/bash
# ARK Banking Demo UAT Test Suite

echo "🧪 Starting ARK Banking Demo UAT Tests"
echo "====================================="

NAMESPACE="demo-bank"
BASE_URL="http://localhost:8000/v1/namespaces/$NAMESPACE"
PASSED=0
FAILED=0

# Helper function to test API endpoint
test_endpoint() {
    local test_name="$1"
    local method="$2"
    local url="$3"
    local data="$4"
    local expected_status="$5"
    
    echo "Testing: $test_name"
    
    if [ "$method" = "POST" ]; then
        response=$(curl -s -w "%{http_code}" -X POST "$url" \
                  -H "Content-Type: application/json" \
                  -d "$data")
    else
        response=$(curl -s -w "%{http_code}" "$url")
    fi
    
    status_code="${response: -3}"
    response_body="${response%???}"
    
    if [ "$status_code" = "$expected_status" ]; then
        echo "✅ PASS: $test_name (Status: $status_code)"
        ((PASSED++))
    else
        echo "❌ FAIL: $test_name (Expected: $expected_status, Got: $status_code)"
        echo "Response: $response_body"
        ((FAILED++))
    fi
    echo
}

# Test 1: Agent Availability
test_endpoint "Agent List" "GET" "$BASE_URL/agents" "" "200"

# Test 2: Individual Agent Queries
test_endpoint "Account Helper Query" "POST" "$BASE_URL/agents/account-helper/query" \
    '{"input": "What is my account balance?"}' "200"

test_endpoint "Loan Advisor Query" "POST" "$BASE_URL/agents/loan-advisor/query" \
    '{"input": "What loans do you offer?"}' "200"

test_endpoint "Inquiry Router Query" "POST" "$BASE_URL/agents/inquiry-router/query" \
    '{"input": "I need help with my account"}' "200"

# Test 3: Team Workflow
test_endpoint "Customer Service Team Query" "POST" "$BASE_URL/teams/customer-service-team/query" \
    '{"input": "I need my balance and loan information"}' "200"

# Test 4: Error Handling
test_endpoint "Non-existent Agent" "POST" "$BASE_URL/agents/fake-agent/query" \
    '{"input": "test"}' "404"

test_endpoint "Invalid JSON" "POST" "$BASE_URL/agents/account-helper/query" \
    '{"invalid": }' "400"

# Test 5: System Health
test_endpoint "System Health" "GET" "http://localhost:8000/health" "" "200"

# Results Summary
echo "📊 UAT Test Results"
echo "==================="
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"
echo "Total Tests: $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo "🎉 All UAT tests passed! System ready for production."
    exit 0
else
    echo "⚠️  Some UAT tests failed. Review and fix before deployment."
    exit 1
fi
```

### **Performance Validation**
```bash
#!/bin/bash
# Performance UAT Tests

echo "⚡ Performance UAT Tests"
echo "======================="

# Test response times
for i in {1..5}; do
    echo "Test $i:"
    time curl -s -X POST "http://localhost:8000/v1/namespaces/demo-bank/queries" \
        -H "Content-Type: application/json" \
        -d '{
          "name": "perf-test-'$i'",
          "input": "What is my account balance?",
          "targets": [{ "type": "agent", "name": "account-helper" }]
        }' > /dev/null
    echo
done

# Test concurrent requests
echo "Testing 10 concurrent requests..."
for i in {1..10}; do
    curl -s -X POST "http://localhost:8000/v1/namespaces/demo-bank/queries" \
        -H "Content-Type: application/json" \
        -d '{
          "name": "concurrent-test-'$i'",
          "input": "Concurrent test '$i'",
          "targets": [{ "type": "agent", "name": "account-helper" }]
        }' &
done
wait
echo "✅ Concurrent test completed"
```

---

## **UAT Success Criteria**

### **Functional Requirements**
- ✅ All agents respond to appropriate queries
- ✅ Team workflows complete successfully  
- ✅ API endpoints return expected HTTP status codes
- ✅ Error handling is graceful and informative
- ✅ Query history is properly recorded

### **Performance Requirements**
- ✅ Individual agent responses < 2 seconds
- ✅ Team workflow responses < 5 seconds
- ✅ System handles 10 concurrent requests
- ✅ No memory leaks or resource exhaustion

### **Integration Requirements**
- ✅ External systems can call ARK APIs
- ✅ Authentication (if enabled) works correctly
- ✅ Proper CORS headers for web integration
- ✅ API documentation matches actual behavior

---

## **Integration with Demo**

During the demo, the API testing phase serves to show:

1. **External Integration Readiness**: "This is how your existing systems would integrate"
2. **Production Readiness**: "We've validated the APIs work reliably"
3. **Developer Experience**: "Simple REST calls, standard HTTP responses"
4. **Monitoring Integration**: "Every API call is tracked and monitored"

The UAT tests prove that ARK is not just a demo, but a production-ready system that external applications can reliably integrate with.
