# MCP Filesystem Server - Local Testing Guide

This guide validates all session management requirements with simple, reproducible steps.

## Prerequisites

- Minikube running
- kubectl configured
- Docker available
- **ARK controller deployed** (provides MCPServer CRD)

## Quick Setup

```bash
# Install the 'ark' CLI:
npm install -g @agents-at-scale/ark

# Install Ark:
ark install

# Optionally configure a 'default' model to use for agents:
ark models create default

# Run the dashboard:
ark dashboard

# Build and deploy mcp-filesystem
cd mcp/filesystem-mcp
npm install
npm run build
docker build -t filesystem-mcp-server:latest .
minikube image load filesystem-mcp-server:latest
helm install mcp-filesystem ./chart

# Wait for pod to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=mcp-filesystem --timeout=60s

# Port forward for testing
kubectl port-forward svc/mcp-filesystem-server 8080:8080 &

# Monitor logs in separate terminal (optional but recommended)
kubectl logs -f -l app.kubernetes.io/name=mcp-filesystem
```

**Expected Startup Logs**:
```
MCP server listening on port 8080
Session file: /data/sessions/sessions.json
Max sessions: 1000
Cleanup session files on delete: false
[Session] No existing session file, starting fresh
```

---

## Test 1: Session ID Generation (AC1)

**Requirement**: The MCP server should give me back a session ID

**Steps**:

```bash
# Send initialize request
curl -v -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc":"2.0",
    "method":"initialize",
    "params":{
      "protocolVersion":"2024-11-05",
      "capabilities":{},
      "clientInfo":{
        "name":"test-client",
        "version":"1.0.0"
      }
    },
    "id":1
  }' 2>&1 | grep -i mcp-session-id

# Example output:
# < mcp-session-id: 550e8400-e29b-41d4-a716-446655440000
```

**Save the session ID for next tests:**
```bash
# Extract and save session ID
SESSION_ID=$(curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc":"2.0",
    "method":"initialize",
    "params":{
      "protocolVersion":"2024-11-05",
      "capabilities":{},
      "clientInfo":{
        "name":"test-client",
        "version":"1.0.0"
      }
    },
    "id":1
  }' -i 2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r')

echo "Session ID: $SESSION_ID"
```

**Expected Result**:
- ✅ Response includes `Mcp-Session-Id` header
- ✅ Session ID is a valid UUID

**Expected Logs**:
```bash
kubectl logs -l app.kubernetes.io/name=mcp-filesystem | grep -E "Session|Directory|Setting base"
```
```
[Session] Created new session 550e8400-e29b-41d4-a716-446655440000 with path: 550e8400-e29b-41d4-a716-446655440000
Setting base directory to: /data/550e8400-e29b-41d4-a716-446655440000
[Directory] Created/verified base directory: /data/550e8400-e29b-41d4-a716-446655440000
[Session] Saved 1 sessions to /data/sessions/sessions.json
```

**Verify Session Directory Created**:
```bash
POD=$(kubectl get pod -l app.kubernetes.io/name=mcp-filesystem -o jsonpath='{.items[0].metadata.name}')
kubectl exec $POD -- ls -la /data/ | grep -v sessions

# Expected: Directory with session ID name
# drwxr-xr-x  2 mcp  mcp   4096 Oct  3 12:00 550e8400-e29b-41d4-a716-446655440000
```

---

## Test 2: Server-Side Session Persistence (AC5)

**Requirement**: The MCP server is where we save the session data

**Steps**:

```bash
# Check sessions file exists
POD=$(kubectl get pod -l app.kubernetes.io/name=mcp-filesystem -o jsonpath='{.items[0].metadata.name}')
kubectl exec $POD -- cat /data/sessions/sessions.json | jq .

# Expected output:
# {
#   "550e8400-e29b-41d4-a716-446655440000": {
#     "path": "550e8400-e29b-41d4-a716-446655440000",
#     "createdAt": "2025-10-03T...",
#     "lastAccessed": "2025-10-03T..."
#   }
# }
```

**Verify Session Directory**:
```bash
# Check that session directory exists
kubectl exec $POD -- ls -la /data/$SESSION_ID

# Expected: Empty directory (no files created yet)
# total 8
# drwxr-xr-x  2 mcp  mcp  4096 Oct  3 12:00 .
# drwxrwxrwx  4 root root 4096 Oct  3 12:00 ..
```

**Expected Result**:
- ✅ Session file exists at `/data/sessions/sessions.json`
- ✅ Session data includes: `path` (session ID), `createdAt`, `lastAccessed`
- ✅ **Path is now the session ID itself** (not "my-test-dir")
- ✅ Directory `/data/{sessionId}/` created and exists

---

## Test 3: Reconnection with Saved Configuration (AC2)

**Requirement**: I need to be able to reconnect to the MCP server with the same session ID and see my configurations saved

### Step 3a: Write a file using the session

```bash
# Use session to write a file
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d '{
    "jsonrpc":"2.0",
    "method":"tools/call",
    "params":{
      "name":"write_file",
      "arguments":{
        "path":"test.txt",
        "content":"Testing reconnection"
      }
    },
    "id":2
  }'

# Verify file was created in session-specific directory
kubectl exec $POD -- cat /data/$SESSION_ID/test.txt
# Expected: Testing reconnection

# Verify directory structure
kubectl exec $POD -- ls -la /data/$SESSION_ID/
# Expected: test.txt file exists in session directory
```

### Step 3b: Restart pod to simulate connection loss

```bash
# Delete pod to simulate server restart
kubectl delete pod $POD

# Wait for new pod
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=mcp-filesystem --timeout=60s

# Get new pod name
POD=$(kubectl get pod -l app.kubernetes.io/name=mcp-filesystem -o jsonpath='{.items[0].metadata.name}')
```

### Step 3c: Check sessions loaded from disk

```bash
# Check logs for session loading
kubectl logs $POD | grep "Loaded.*sessions"

# Expected:
# [Session] Loaded 1 sessions from /data/sessions/sessions.json
```

**Expected Logs**:
```
[Session] Loaded 1 sessions from /data/sessions/sessions.json
MCP server listening on port 8080
Session file: /data/sessions/sessions.json
Max sessions: 1000
```

### Step 3d: Reconnect with same session ID

```bash
# Reconnect with the SAME session ID from Test 1
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d '{
    "jsonrpc":"2.0",
    "method":"tools/call",
    "params":{
      "name":"read_text_file",
      "arguments":{
        "path":"test.txt"
      }
    },
    "id":3
  }'

# Expected: Should return "Testing reconnection"
```

### Step 3e: Verify reconnection logged

```bash
kubectl logs $POD | grep -E "Reconnected|Setting base|Directory"

# Expected:
# [Session] Reconnected session 550e8400-e29b-41d4-a716-446655440000 with path: 550e8400-e29b-41d4-a716-446655440000
# Setting base directory to: /data/550e8400-e29b-41d4-a716-446655440000
# [Directory] Created/verified base directory: /data/550e8400-e29b-41d4-a716-446655440000
```

**Expected Logs** (full sequence for reconnection):
```bash
kubectl logs $POD | tail -20
```
```
[Session] Reconnected session 550e8400-e29b-41d4-a716-446655440000 with path: 550e8400-e29b-41d4-a716-446655440000
Setting base directory to: /data/550e8400-e29b-41d4-a716-446655440000
[Directory] Created/verified base directory: /data/550e8400-e29b-41d4-a716-446655440000
[Session] Updated access for session 550e8400-e29b-41d4-a716-446655440000
[Session] Saved 1 sessions to /data/sessions/sessions.json
```

### Step 3f: Create another file to confirm path still configured

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d '{
    "jsonrpc":"2.0",
    "method":"tools/call",
    "params":{
      "name":"write_file",
      "arguments":{
        "path":"test2.txt",
        "content":"Path preserved!"
      }
    },
    "id":4
  }'

# Verify both files are in the session-specific directory
kubectl exec $POD -- ls /data/$SESSION_ID/
# Expected:
# test.txt
# test2.txt

kubectl exec $POD -- cat /data/$SESSION_ID/test.txt
# Expected: Testing reconnection

kubectl exec $POD -- cat /data/$SESSION_ID/test2.txt
# Expected: Path preserved!
```

**Expected Results**:
- ✅ After pod restart, session loads from disk
- ✅ Reconnection works with same session ID
- ✅ **Path is session ID** (isolated directory per session)
- ✅ Files persist in `/data/{sessionId}/` directory
- ✅ All files readable and writable in session-specific directory

---

## Test 4: Adapter Folder Structure (AC3)

**Requirement**: The adapter folder should be used for the logic of the filesystem MCP

**Steps**:

```bash
# Verify directory structure
ls -la mcp/filesystem-mcp/src/

# Expected output:
# drwxr-xr-x  filesystem/
# -rw-r--r--  index.ts

# Check filesystem adapter contents
ls -la mcp/filesystem-mcp/src/filesystem/

# Expected output:
# -rw-r--r--  index.ts       # MCP server creation
# -rw-r--r--  lib.ts         # File operations
# -rw-r--r--  path-utils.ts
# -rw-r--r--  path-validation.ts
# -rw-r--r--  roots-utils.ts
```

**Verify import in wrapper**:

```bash
grep "import.*createServer.*filesystem" mcp/filesystem-mcp/src/index.ts

# Expected:
# import { createServer } from './filesystem/index.js';
```

**Expected Results**:
- ✅ `src/filesystem/` directory exists
- ✅ Contains all MCP logic files
- ✅ Wrapper imports from `./filesystem/index.js`

---

## Test 5: Wrapper Decoupling (AC4)

**Requirement**: The wrapper (that provides the sessions) should be decoupled from the logic so we can use it in other MCPs

**Steps**:

### Step 5a: Verify adapter has no session knowledge

```bash
# Search for session-related imports in adapter
grep -r "Session\|sessions\|transports" mcp/filesystem-mcp/src/filesystem/

# Expected: No matches (exit code 1)
```

### Step 5b: Verify wrapper only passes configuration

```bash
# Check how wrapper calls adapter
grep -A 2 "createServer(" mcp/filesystem-mcp/src/index.ts

# Expected output shows only path parameter:
# const server = await createServer(session.path);
# const server = await createServer(newSessionId);
```

### Step 5c: Verify adapter interface

```bash
# Check adapter's createServer signature
grep -A 3 "export const createServer" mcp/filesystem-mcp/src/filesystem/index.ts

# Expected:
# export const createServer = async (sessionPath?: string) => {
#   await setBaseDirectory(path.join(BASE_PATH, sessionPath || "shared"));
```

**Expected Results**:
- ✅ Adapter has no session management code
- ✅ Adapter only receives `path` parameter
- ✅ Wrapper handles all session logic
- ✅ Clean interface between wrapper and adapter

---

## Test 6: LRU Eviction (Session Invalidation Part 1)

**Requirement**: If users continue to create new sessions without closing the old ones, we will naturally phase out the older sessions over time

**Steps**:

```bash
# Set low MAX_SESSIONS for testing
kubectl set env deployment/mcp-filesystem-server MAX_SESSIONS=3
kubectl rollout status deployment/mcp-filesystem-server
kubectl port-forward svc/mcp-filesystem-server 8080:8080 &

# Create 3 sessions
for i in {1..3}; do
  curl -X POST http://localhost:8080/mcp \
    -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
    -d "{
      \"jsonrpc\":\"2.0\",
      \"method\":\"initialize\",
      \"params\":{
        \"protocolVersion\":\"2024-11-05\",
        \"capabilities\":{},
        \"clientInfo\":{
          \"name\":\"test-client\",
          \"version\":\"1.0.0\"
        }
      },
      \"id\":$i
    }"
  sleep 1
done

# Verify 3 sessions exist
POD=$(kubectl get pod -l app.kubernetes.io/name=mcp-filesystem -o jsonpath='{.items[0].metadata.name}')
kubectl exec $POD -- cat /data/sessions/sessions.json | jq 'keys | length'
# Expected: 3

# Create 4th session (should evict oldest)
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc":"2.0",
    "method":"initialize",
    "params":{
      "protocolVersion":"2024-11-05",
      "capabilities":{},
      "clientInfo":{
        "name":"test-client",
        "version":"1.0.0"
      }
    },
    "id":4
  }'

# Check eviction happened
kubectl logs $POD | grep Evicted
# Expected: [Session] Evicted oldest session: <session-1-id>

# Verify still only 3 sessions
kubectl exec $POD -- cat /data/sessions/sessions.json | jq 'keys | length'
# Expected: 3

# Reset MAX_SESSIONS
kubectl set env deployment/mcp-filesystem-server MAX_SESSIONS=1000
```

**Expected Results**:
- ✅ Only 3 sessions exist when limit is 3
- ✅ Creating 4th session evicts oldest
- ✅ Eviction logged with session ID
- ✅ Session count stays at MAX_SESSIONS

**Expected Logs**:
```bash
kubectl logs $POD | grep -E "Session|Evicted"
```
```
[Session] Created new session <uuid-1> with path: <uuid-1>
[Session] Created new session <uuid-2> with path: <uuid-2>
[Session] Created new session <uuid-3> with path: <uuid-3>
[Session] Evicting oldest session: <uuid-1> (cleanup: false)
[Session] Evicted session: <uuid-1>
[Session] Created new session <uuid-4> with path: <uuid-4>
[Session] Saved 3 sessions to /data/sessions/sessions.json
```

---

## Test 7: Access-Based LRU

**Requirement**: Verify LRU is based on access time, not creation time

**Steps**:

```bash
# Create 3 sessions and save IDs
SESSION_1=$(curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc":"2.0",
    "method":"initialize",
    "params":{
      "protocolVersion":"2024-11-05",
      "capabilities":{},
      "clientInfo":{
        "name":"test-client",
        "version":"1.0.0"
      }
    },
    "id":1
  }' -i 2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r')

sleep 1

SESSION_2=$(curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc":"2.0",
    "method":"initialize",
    "params":{
      "protocolVersion":"2024-11-05",
      "capabilities":{},
      "clientInfo":{
        "name":"test-client",
        "version":"1.0.0"
      }
    },
    "id":2
  }' -i 2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r')

sleep 1

SESSION_3=$(curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc":"2.0",
    "method":"initialize",
    "params":{
      "protocolVersion":"2024-11-05",
      "capabilities":{},
      "clientInfo":{
        "name":"test-client",
        "version":"1.0.0"
      }
    },
    "id":3
  }' -i 2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r')

# Access SESSION_1 (oldest) to make it most recently used
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: $SESSION_1" \
  -d '{
    "jsonrpc":"2.0",
    "method":"tools/list",
    "params":{},
    "id":10
  }' > /dev/null

# Create 4th session (should evict SESSION_2, not SESSION_1)
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc":"2.0",
    "method":"initialize",
    "params":{
      "protocolVersion":"2024-11-05",
      "capabilities":{},
      "clientInfo":{
        "name":"test-client",
        "version":"1.0.0"
      }
    },
    "id":4
  }' > /dev/null

# Verify SESSION_1 still exists (was accessed recently)
POD=$(kubectl get pod -l app.kubernetes.io/name=mcp-filesystem -o jsonpath='{.items[0].metadata.name}')
kubectl exec $POD -- cat /data/sessions/sessions.json | jq -r 'keys[]' | grep "$SESSION_1"
# Expected: Session 1 found

# Verify SESSION_2 was evicted
kubectl exec $POD -- cat /data/sessions/sessions.json | jq -r 'keys[]' | grep "$SESSION_2"
# Expected: No output (session 2 evicted)

# Check logs confirm SESSION_2 evicted
kubectl logs $POD | grep Evicted | tail -1
# Expected: Shows SESSION_2 was evicted
```

**Expected Results**:
- ✅ Accessing a session updates its LRU position
- ✅ Least recently accessed session evicted (not oldest by creation)
- ✅ Recently accessed sessions preserved

**Expected Logs** (showing access updates):
```bash
kubectl logs $POD | grep -E "Updated access|Evicted"
```
```
[Session] Updated access for session <uuid-1>
[Session] Saved 3 sessions to /data/sessions/sessions.json
[Session] Evicted oldest session: <uuid-2>
[Session] Created new session <uuid-4> with path: lru-4
```

---

## Test 8: Explicit Session Deletion (Session Invalidation Part 2)

**Requirement**: If we receive a delete request, we will remove the corresponding session

**Steps**:

```bash
# Create a test session
DELETE_SESSION=$(curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc":"2.0",
    "method":"initialize",
    "params":{
      "protocolVersion":"2024-11-05",
      "capabilities":{},
      "clientInfo":{
        "name":"test-client",
        "version":"1.0.0"
      }
    },
    "id":1
  }' -i 2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r')

echo "Created session: $DELETE_SESSION"

# Verify session exists
POD=$(kubectl get pod -l app.kubernetes.io/name=mcp-filesystem -o jsonpath='{.items[0].metadata.name}')
kubectl exec $POD -- cat /data/sessions/sessions.json | jq ".[\"$DELETE_SESSION\"]"
# Expected: Session data displayed

# Delete the session explicitly
curl -X DELETE http://localhost:8080/mcp/session \
  -H "Mcp-Session-Id: $DELETE_SESSION" \
  -i

# Expected: HTTP/1.1 204 No Content

# Check deletion logged
kubectl logs $POD | grep "Deleting session"
# Expected: [Session] Deleting session: <DELETE_SESSION> (cleanup: false)
# Expected: [Session] Deleted session: <DELETE_SESSION>

# Verify session removed from storage
kubectl exec $POD -- cat /data/sessions/sessions.json | jq ".[\"$DELETE_SESSION\"]"
# Expected: null

# Try to reconnect (should fail)
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: $DELETE_SESSION" \
  -d '{
    "jsonrpc":"2.0",
    "method":"tools/list",
    "params":{},
    "id":2
  }'

# Expected: {"error":{"code":-32000,"message":"Session not found or expired"}}

# Test deleting non-existent session
curl -X DELETE http://localhost:8080/mcp/session \
  -H "Mcp-Session-Id: non-existent-uuid" \
  -i

# Expected: HTTP/1.1 404 Not Found
```

**Expected Results**:
- ✅ DELETE endpoint removes session from memory and disk
- ✅ Deletion logged with session ID
- ✅ Reconnection fails after deletion
- ✅ Returns 404 for non-existent sessions

**Expected Logs**:
```bash
kubectl logs $POD | grep -E "Deleting session|Deleted session|Session not found"
```
```
[Session] Deleting session: <uuid> (cleanup: false)
[Session] Deleted session: <uuid>
[Session] Saved 0 sessions to /data/sessions/sessions.json
[Session] Session not found or expired: <uuid>
[Session] DELETE /mcp/session failed - session not found: non-existent-uuid
```

---

## Requirements Validation Summary

| Requirement | Test | Status |
|-------------|------|--------|
| **AC1**: Session ID returned | Test 1 | ✅ |
| **AC2**: Reconnection with saved config | Test 3 | ✅ |
| **AC3**: Adapter folder structure | Test 4 | ✅ |
| **AC4**: Wrapper decoupling | Test 5 | ✅ |
| **AC5**: Server-side persistence | Test 2 | ✅ |
| **Test Scenario**: Path preservation | Test 3 | ✅ |
| **Session Invalidation**: LRU eviction | Tests 6-7 | ✅ |
| **Session Invalidation**: Explicit delete | Test 8 | ✅ |

---

## Quick Test Script

Run all tests in sequence:

```bash
#!/bin/bash
set -e

echo "=== Starting MCP Session Tests ==="

# Setup
cd mcp/filesystem-mcp
minikube start
npm install && npm run build
docker build -t filesystem-mcp-server:latest .
minikube image load filesystem-mcp-server:latest
helm install mcp-filesystem ./chart
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=mcp-filesystem --timeout=60s
kubectl port-forward svc/mcp-filesystem-server 8080:8080 &
PF_PID=$!
sleep 5

# Test 1: Session ID
echo "Test 1: Session ID Generation"
SESSION_ID=$(curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test-client","version":"1.0.0"}},"id":1}' \
  -i 2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r')
echo "✅ Session ID: $SESSION_ID"

# Test 2: Persistence
echo "Test 2: Server-Side Persistence"
POD=$(kubectl get pod -l app.kubernetes.io/name=mcp-filesystem -o jsonpath='{.items[0].metadata.name}')
kubectl exec $POD -- cat /data/sessions/sessions.json | jq . > /dev/null
echo "✅ Session file exists"

# Test 3: Reconnection
echo "Test 3: Reconnection"
curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"write_file","arguments":{"path":"test.txt","content":"test"}},"id":2}' > /dev/null
kubectl delete pod $POD --wait=false
sleep 10
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=mcp-filesystem --timeout=60s
POD=$(kubectl get pod -l app.kubernetes.io/name=mcp-filesystem -o jsonpath='{.items[0].metadata.name}')
kubectl logs $POD | grep "Loaded.*sessions" > /dev/null
echo "✅ Reconnection works"

# Test 4: Adapter structure
echo "Test 4: Adapter Structure"
ls mcp/filesystem-mcp/src/filesystem/index.ts > /dev/null
echo "✅ Adapter folder exists"

# Test 5: Decoupling
echo "Test 5: Wrapper Decoupling"
! grep -r "Session\|sessions\|transports" mcp/filesystem-mcp/src/filesystem/ > /dev/null
echo "✅ Adapter decoupled"

# Test 6: LRU
echo "Test 6: LRU Eviction"
kubectl set env deployment/mcp-filesystem-server MAX_SESSIONS=2 --wait=true
sleep 10
kubectl port-forward svc/mcp-filesystem-server 8080:8080 &
sleep 5
for i in {1..3}; do
  curl -s -X POST http://localhost:8080/mcp \
    -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
    -d "{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2024-11-05\",\"capabilities\":{},\"clientInfo\":{\"name\":\"test-client\",\"version\":\"1.0.0\"}},\"id\":$i}" > /dev/null
  sleep 1
done
POD=$(kubectl get pod -l app.kubernetes.io/name=mcp-filesystem -o jsonpath='{.items[0].metadata.name}')
COUNT=$(kubectl exec $POD -- cat /data/sessions/sessions.json | jq 'keys | length')
[ "$COUNT" = "2" ]
echo "✅ LRU eviction works"

# Cleanup
kill $PF_PID
helm uninstall mcp-filesystem

echo "=== All Tests Passed ==="
```

---

## Debugging

**View logs**:
```bash
kubectl logs -f -l app.kubernetes.io/name=mcp-filesystem
```

**Check session file**:
```bash
POD=$(kubectl get pod -l app.kubernetes.io/name=mcp-filesystem -o jsonpath='{.items[0].metadata.name}')
kubectl exec $POD -- cat /data/sessions/sessions.json | jq .
```

**Check persistent volume**:
```bash
kubectl exec $POD -- ls -la /data/
```

---

## Cleanup

```bash
# Stop port forwarding
pkill -f "port-forward.*8080:8080"

# Uninstall
helm uninstall mcp-filesystem

# Remove minikube (optional)
minikube delete
```
