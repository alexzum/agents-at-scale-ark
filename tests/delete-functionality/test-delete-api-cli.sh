#!/usr/bin/env bash
set -euo pipefail

# Test cases for Delete API and CLI functionality
# This script tests the delete endpoints and CLI commands added in the feat/delete-query branch

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../" && pwd)"

# Test configuration
API_BASE_URL="http://localhost:8080"
CLI_BINARY="ark"
TEST_NAMESPACE="test-delete-$(date +%s)"
TEST_TIMEOUT=30

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

run_test() {
    local test_name="$1"
    local test_function="$2"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    log_info "Running test: $test_name"
    
    if $test_function; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        log_success "✓ PASSED: $test_name"
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        log_error "✗ FAILED: $test_name"
    fi
    echo
}

# API Test Helper Functions
api_request() {
    local method="$1"
    local endpoint="$2"
    local data="${3:-}"
    local expected_status="${4:-200}"
    
    local curl_cmd="curl -s -w '%{http_code}' -X $method"
    
    if [ -n "$data" ]; then
        curl_cmd="$curl_cmd -H 'Content-Type: application/json' -d '$data'"
    fi
    
    curl_cmd="$curl_cmd '$API_BASE_URL$endpoint'"
    
    local response
    response=$(eval "$curl_cmd")
    local status_code="${response: -3}"
    local body="${response%???}"
    
    if [ "$status_code" = "$expected_status" ]; then
        echo "$body"
        return 0
    else
        log_error "API request failed: $method $endpoint"
        log_error "Expected status: $expected_status, Got: $status_code"
        log_error "Response: $body"
        return 1
    fi
}

# CLI Test Helper Functions
cli_command() {
    local cmd="$1"
    local expected_exit_code="${2:-0}"
    
    log_info "Running CLI command: $cmd"
    
    if eval "$cmd" >/dev/null 2>&1; then
        local exit_code=$?
        if [ $exit_code -eq $expected_exit_code ]; then
            return 0
        else
            log_error "CLI command failed with exit code: $exit_code (expected: $expected_exit_code)"
            return 1
        fi
    else
        local exit_code=$?
        if [ $exit_code -eq $expected_exit_code ]; then
            return 0
        else
            log_error "CLI command failed with exit code: $exit_code (expected: $expected_exit_code)"
            return 1
        fi
    fi
}

# Test Data Creation Functions
create_test_model() {
    local model_name="$1"
    local model_data='{
        "type": "azure",
        "model": {"value": "gpt-4"},
        "config": {
            "azure": {
                "baseUrl": {"value": "https://test.openai.azure.com/"},
                "apiKey": {"valueFrom": {"secretKeyRef": {"name": "test-secret", "key": "api-key"}}},
                "apiVersion": {"value": "2024-12-01-preview"}
            }
        }
    }'
    
    api_request "POST" "/v1/models" "$model_data" "201"
}

create_test_agent() {
    local agent_name="$1"
    local agent_data='{
        "model": {"value": "test-model"},
        "prompt": {"value": "You are a helpful assistant"},
        "tools": []
    }'
    
    api_request "POST" "/v1/agents" "$agent_data" "201"
}

create_test_tool() {
    local tool_name="$1"
    local tool_data='{
        "type": "function",
        "function": {
            "name": "test_function",
            "description": "A test function",
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "Input parameter"}
                },
                "required": ["input"]
            }
        }
    }'
    
    api_request "POST" "/v1/tools" "$tool_data" "201"
}

create_test_team() {
    local team_name="$1"
    local team_data='{
        "strategy": {"type": "sequential"},
        "members": [{"name": "test-agent", "role": "primary"}]
    }'
    
    api_request "POST" "/v1/teams" "$team_data" "201"
}

create_test_query() {
    local query_name="$1"
    local query_data='{
        "target": {"type": "agent", "name": "test-agent"},
        "input": {"value": "Hello, how are you?"}
    }'
    
    api_request "POST" "/v1/queries" "$query_data" "201"
}

# API Delete Tests
test_delete_model_api() {
    local model_name="test-model-$(date +%s)"
    
    # Create model
    create_test_model "$model_name" || return 1
    
    # Delete model
    api_request "DELETE" "/v1/models/$model_name" "" "204" || return 1
    
    # Verify deletion
    api_request "GET" "/v1/models/$model_name" "" "404" || return 1
    
    return 0
}

test_delete_agent_api() {
    local agent_name="test-agent-$(date +%s)"
    
    # Create agent
    create_test_agent "$agent_name" || return 1
    
    # Delete agent
    api_request "DELETE" "/v1/agents/$agent_name" "" "204" || return 1
    
    # Verify deletion
    api_request "GET" "/v1/agents/$agent_name" "" "404" || return 1
    
    return 0
}

test_delete_tool_api() {
    local tool_name="test-tool-$(date +%s)"
    
    # Create tool
    create_test_tool "$tool_name" || return 1
    
    # Delete tool
    api_request "DELETE" "/v1/tools/$tool_name" "" "204" || return 1
    
    # Verify deletion
    api_request "GET" "/v1/tools/$tool_name" "" "404" || return 1
    
    return 0
}

test_delete_team_api() {
    local team_name="test-team-$(date +%s)"
    
    # Create team
    create_test_team "$team_name" || return 1
    
    # Delete team
    api_request "DELETE" "/v1/teams/$team_name" "" "204" || return 1
    
    # Verify deletion
    api_request "GET" "/v1/teams/$team_name" "" "404" || return 1
    
    return 0
}

test_delete_query_api() {
    local query_name="test-query-$(date +%s)"
    
    # Create query
    create_test_query "$query_name" || return 1
    
    # Delete query
    api_request "DELETE" "/v1/queries/$query_name" "" "204" || return 1
    
    # Verify deletion
    api_request "GET" "/v1/queries/$query_name" "" "404" || return 1
    
    return 0
}

test_delete_session_api() {
    local session_id="test-session-$(date +%s)"
    
    # Create session (if session creation endpoint exists)
    # For now, we'll test deletion of non-existent session
    api_request "DELETE" "/v1/sessions/$session_id" "" "404" || return 1
    
    return 0
}

test_delete_all_sessions_api() {
    # Test delete all sessions endpoint
    api_request "DELETE" "/v1/sessions" "" "200" || return 1
    
    return 0
}

test_delete_query_messages_api() {
    local session_id="test-session-$(date +%s)"
    local query_id="test-query-$(date +%s)"
    
    # Test deletion of query messages
    api_request "DELETE" "/v1/sessions/$session_id/queries/$query_id/messages" "" "404" || return 1
    
    return 0
}

# CLI Delete Tests
test_cli_memory_reset_session() {
    local session_id="test-session-$(date +%s)"
    
    # Test CLI command for deleting a session
    cli_command "$CLI_BINARY memory reset session $session_id" || return 1
    
    return 0
}

test_cli_memory_reset_query() {
    local session_id="test-session-$(date +%s)"
    local query_id="test-query-$(date +%s)"
    
    # Test CLI command for deleting query messages
    cli_command "$CLI_BINARY memory reset query $session_id $query_id" || return 1
    
    return 0
}

test_cli_memory_reset_all() {
    # Test CLI command for deleting all sessions
    cli_command "$CLI_BINARY memory reset all" || return 1
    
    return 0
}

test_cli_memory_list() {
    # Test CLI command for listing sessions
    cli_command "$CLI_BINARY memory list" || return 1
    
    return 0
}

# Error Handling Tests
test_delete_nonexistent_resource() {
    local resource_name="nonexistent-$(date +%s)"
    
    # Test deleting non-existent model
    api_request "DELETE" "/v1/models/$resource_name" "" "404" || return 1
    
    # Test deleting non-existent agent
    api_request "DELETE" "/v1/agents/$resource_name" "" "404" || return 1
    
    # Test deleting non-existent tool
    api_request "DELETE" "/v1/tools/$resource_name" "" "404" || return 1
    
    return 0
}

test_delete_with_invalid_namespace() {
    local model_name="test-model-$(date +%s)"
    
    # Create model in default namespace
    create_test_model "$model_name" || return 1
    
    # Try to delete from invalid namespace
    api_request "DELETE" "/v1/models/$model_name?namespace=invalid-namespace" "" "404" || return 1
    
    # Clean up
    api_request "DELETE" "/v1/models/$model_name" "" "204" || true
    
    return 0
}

# Integration Tests
test_delete_cascade_effects() {
    local model_name="test-model-$(date +%s)"
    local agent_name="test-agent-$(date +%s)"
    
    # Create model and agent that depends on it
    create_test_model "$model_name" || return 1
    create_test_agent "$agent_name" || return 1
    
    # Delete the model
    api_request "DELETE" "/v1/models/$model_name" "" "204" || return 1
    
    # Verify agent still exists (should not cascade delete)
    api_request "GET" "/v1/agents/$agent_name" "" "200" || return 1
    
    # Clean up agent
    api_request "DELETE" "/v1/agents/$agent_name" "" "204" || true
    
    return 0
}

test_delete_with_active_queries() {
    local agent_name="test-agent-$(date +%s)"
    local query_name="test-query-$(date +%s)"
    
    # Create agent and query
    create_test_agent "$agent_name" || return 1
    create_test_query "$query_name" || return 1
    
    # Try to delete agent with active query
    api_request "DELETE" "/v1/agents/$agent_name" "" "204" || return 1
    
    # Verify query still exists
    api_request "GET" "/v1/queries/$query_name" "" "200" || return 1
    
    # Clean up
    api_request "DELETE" "/v1/queries/$query_name" "" "204" || true
    
    return 0
}

# Performance Tests
test_delete_performance() {
    local start_time
    local end_time
    local duration
    
    # Test delete performance with multiple resources
    start_time=$(date +%s.%N)
    
    for i in {1..5}; do
        local model_name="perf-test-model-$i-$(date +%s)"
        create_test_model "$model_name" || return 1
        api_request "DELETE" "/v1/models/$model_name" "" "204" || return 1
    done
    
    end_time=$(date +%s.%N)
    duration=$(echo "$end_time - $start_time" | bc)
    
    log_info "Delete performance test completed in ${duration}s"
    
    # Performance should be reasonable (less than 10 seconds for 5 operations)
    if (( $(echo "$duration < 10" | bc -l) )); then
        return 0
    else
        log_warn "Delete performance test took longer than expected: ${duration}s"
        return 1
    fi
}

# Cleanup function
cleanup() {
    log_info "Cleaning up test resources..."
    
    # Clean up any remaining test resources
    kubectl delete namespace "$TEST_NAMESPACE" --ignore-not-found=true || true
    
    log_info "Cleanup complete"
}

# Main test execution
main() {
    log_info "Starting Delete API and CLI tests..."
    log_info "API Base URL: $API_BASE_URL"
    log_info "CLI Binary: $CLI_BINARY"
    log_info "Test Namespace: $TEST_NAMESPACE"
    echo
    
    # Check prerequisites
    if ! command -v curl >/dev/null 2>&1; then
        log_error "curl not found. Please install curl."
        exit 1
    fi
    
    if ! command -v kubectl >/dev/null 2>&1; then
        log_error "kubectl not found. Please install kubectl."
        exit 1
    fi
    
    if ! command -v bc >/dev/null 2>&1; then
        log_error "bc not found. Please install bc."
        exit 1
    fi
    
    # Create test namespace
    kubectl create namespace "$TEST_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Run API tests
    log_info "=== Running API Delete Tests ==="
    run_test "Delete Model API" test_delete_model_api
    run_test "Delete Agent API" test_delete_agent_api
    run_test "Delete Tool API" test_delete_tool_api
    run_test "Delete Team API" test_delete_team_api
    run_test "Delete Query API" test_delete_query_api
    run_test "Delete Session API" test_delete_session_api
    run_test "Delete All Sessions API" test_delete_all_sessions_api
    run_test "Delete Query Messages API" test_delete_query_messages_api
    
    # Run CLI tests
    log_info "=== Running CLI Delete Tests ==="
    run_test "CLI Memory Reset Session" test_cli_memory_reset_session
    run_test "CLI Memory Reset Query" test_cli_memory_reset_query
    run_test "CLI Memory Reset All" test_cli_memory_reset_all
    run_test "CLI Memory List" test_cli_memory_list
    
    # Run error handling tests
    log_info "=== Running Error Handling Tests ==="
    run_test "Delete Non-existent Resource" test_delete_nonexistent_resource
    run_test "Delete with Invalid Namespace" test_delete_with_invalid_namespace
    
    # Run integration tests
    log_info "=== Running Integration Tests ==="
    run_test "Delete Cascade Effects" test_delete_cascade_effects
    run_test "Delete with Active Queries" test_delete_with_active_queries
    
    # Run performance tests
    log_info "=== Running Performance Tests ==="
    run_test "Delete Performance" test_delete_performance
    
    # Print results
    echo "=========================================="
    log_info "Test Results:"
    log_info "Total tests run: $TESTS_RUN"
    log_info "Tests passed: $TESTS_PASSED"
    log_info "Tests failed: $TESTS_FAILED"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        log_success "All tests passed! ✓"
        exit 0
    else
        log_error "Some tests failed! ✗"
        exit 1
    fi
}

# Trap to ensure cleanup on exit
trap cleanup EXIT

# Run main function
main "$@"
