import express from 'express';
import { randomUUID } from 'node:crypto';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { isInitializeRequest } from '@modelcontextprotocol/sdk/types.js';
import { createServer } from './filesystem/index.js';
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { rm } from 'fs/promises';
import { dirname } from 'path';

export type Session = {
  path: string;
  createdAt: string;
  lastAccessed: string;
};

const PORT = process.env.PORT ? parseInt(process.env.PORT) : 8080;
const SESSION_FILE = process.env.SESSION_FILE || '/data/sessions/sessions.json';
const MAX_SESSIONS = parseInt(process.env.MAX_SESSIONS || '1000');
const CLEANUP_SESSION_FILES = process.env.CLEANUP_SESSION_FILES === 'true';
const DATA_ROOT = '/data';

const app = express();
app.use(express.json());

const sessions = new Map<string, Session>();
const transports: { [sessionId: string]: StreamableHTTPServerTransport } = {};
const servers: { [sessionId: string]: Server } = {};
const sessionAccessOrder: string[] = [];

function loadSessions(): void {
  if (!existsSync(SESSION_FILE)) {
    console.log('[Session] No existing session file, starting fresh');
    return;
  }

  try {
    const data = readFileSync(SESSION_FILE, 'utf-8');
    const parsed = JSON.parse(data);

    for (const [id, session] of Object.entries(parsed)) {
      sessions.set(id, session as Session);
      sessionAccessOrder.push(id);
    }

    console.log(`[Session] Loaded ${sessions.size} sessions from ${SESSION_FILE}`);
  } catch (error) {
    console.error('[Session] Failed to load sessions:', error);
  }
}

function saveSessions(): void {
  try {
    const dir = dirname(SESSION_FILE);
    if (!existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }

    const data = Object.fromEntries(sessions);
    writeFileSync(SESSION_FILE, JSON.stringify(data, null, 2));
    console.log(`[Session] Saved ${sessions.size} sessions to ${SESSION_FILE}`);
  } catch (error) {
    console.error('[Session] Failed to save sessions:', error);
  }
}

async function cleanupSessionDirectory(sessionPath: string): Promise<void> {
  try {
    const dirPath = `${DATA_ROOT}/${sessionPath}`;
    await rm(dirPath, { recursive: true, force: true });
    console.log(`[Session] Cleaned up directory: ${dirPath}`);
  } catch (error) {
    console.error(`[Session] Failed to cleanup directory ${sessionPath}:`, error);
  }
}

function updateSessionAccess(sessionId: string): void {
  const index = sessionAccessOrder.indexOf(sessionId);
  if (index !== -1) {
    sessionAccessOrder.splice(index, 1);
  }
  sessionAccessOrder.push(sessionId);

  const session = sessions.get(sessionId);
  if (session) {
    session.lastAccessed = new Date().toISOString();
    sessions.set(sessionId, session);
    console.log(`[Session] Updated access for session ${sessionId}`);
    saveSessions();
  }
}

async function evictOldestSession(): Promise<void> {
  if (sessionAccessOrder.length === 0) return;

  const oldestSessionId = sessionAccessOrder[0];
  const session = sessions.get(oldestSessionId);

  console.log(`[Session] Evicting oldest session: ${oldestSessionId} (cleanup: ${CLEANUP_SESSION_FILES})`);

  sessionAccessOrder.shift();
  sessions.delete(oldestSessionId);
  saveSessions();

  if (CLEANUP_SESSION_FILES && session?.path) {
    await cleanupSessionDirectory(session.path);
  }

  console.log(`[Session] Evicted session: ${oldestSessionId}`);
}

async function deleteSession(sessionId: string): Promise<void> {
  const session = sessions.get(sessionId);

  console.log(`[Session] Deleting session: ${sessionId} (cleanup: ${CLEANUP_SESSION_FILES})`);

  delete transports[sessionId];
  delete servers[sessionId];
  sessions.delete(sessionId);

  const index = sessionAccessOrder.indexOf(sessionId);
  if (index !== -1) {
    sessionAccessOrder.splice(index, 1);
  }

  if (CLEANUP_SESSION_FILES && session?.path) {
    await cleanupSessionDirectory(session.path);
  }

  saveSessions();
  console.log(`[Session] Deleted session: ${sessionId}`);
}

loadSessions();

app.post('/mcp', async (req, res) => {
  const sessionId = (req.headers['Mcp-Session-Id'] ??
    req.headers['mcp-session-id']) as string | undefined;
  let transport: StreamableHTTPServerTransport;

  if (sessionId && transports[sessionId] && servers[sessionId]) {
    transport = transports[sessionId];
    console.log(`[Session] Reusing existing transport and server for session ${sessionId}`);
    updateSessionAccess(sessionId);
  } else if (sessionId && transports[sessionId] && !servers[sessionId]) {
    const session = sessions.get(sessionId);
    if (!session) {
      console.log(`[Session] Session not found or expired: ${sessionId}`);
      res.status(400).json({
        jsonrpc: '2.0',
        error: {
          code: -32000,
          message: 'Session not found or expired',
        },
        id: null,
      });
      return;
    }

    transport = transports[sessionId];
    console.log(`[Session] Transport exists but server missing for session ${sessionId}, recreating server`);

    const server = await createServer(session.path);
    servers[sessionId] = server;
    await server.connect(transport);
    updateSessionAccess(sessionId);
  } else if (sessionId && !transports[sessionId]) {
    const session = sessions.get(sessionId);

    if (!session) {
      console.log(`[Session] Session not found or expired: ${sessionId}`);
      res.status(400).json({
        jsonrpc: '2.0',
        error: {
          code: -32000,
          message: 'Session not found or expired',
        },
        id: null,
      });
      return;
    }

    transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: () => sessionId,
      onsessioninitialized: () => {
        transports[sessionId] = transport;
      },
    });

    transport.onclose = () => {
      delete transports[sessionId];
      delete servers[sessionId];
      console.log(`[Transport] Closed session ${sessionId}, session data kept for reconnection`);
    };

    const server = await createServer(session.path);
    servers[sessionId] = server;
    await server.connect(transport);
    updateSessionAccess(sessionId);

    console.log(`[Session] Reconnected session ${sessionId} with path: ${session.path || 'default'}`);
  } else if (!sessionId && isInitializeRequest(req.body)) {
    if (sessions.size >= MAX_SESSIONS) {
      await evictOldestSession();
    }

    const newSessionId = randomUUID();
    const now = new Date().toISOString();
    const session: Session = {
      path: newSessionId,
      createdAt: now,
      lastAccessed: now,
    };

    sessions.set(newSessionId, session);
    sessionAccessOrder.push(newSessionId);
    saveSessions();

    console.log(`[Session] Created new session ${newSessionId} with path: ${session.path}`);

    transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: () => newSessionId,
      onsessioninitialized: sessionId => {
        transports[sessionId] = transport;
      },
    });

    transport.onclose = () => {
      if (transport.sessionId) {
        delete transports[transport.sessionId];
        delete servers[transport.sessionId];
        console.log(`[Transport] Closed session ${transport.sessionId}, session data kept for reconnection`);
      }
    };

    const server = await createServer(newSessionId);
    servers[newSessionId] = server;

    await server.connect(transport);
  } else {
    res.status(400).json({
      jsonrpc: '2.0',
      error: {
        code: -32000,
        message: 'Bad Request: No valid session ID provided',
      },
      id: null,
    });
    return;
  }

  await transport.handleRequest(req, res, req.body);
});

const handleSessionRequest = async (
  req: express.Request,
  res: express.Response
) => {
  const sessionId = (req.headers['Mcp-Session-Id'] ??
    req.headers['mcp-session-id']) as string | undefined;
  if (!sessionId || !transports[sessionId]) {
    console.log(`[Session] Invalid or missing session ID in ${req.method} ${req.path}`);
    res.status(400).send('Invalid or missing session ID');
    return;
  }
  const transport = transports[sessionId];
  updateSessionAccess(sessionId);
  await transport.handleRequest(req, res);
};
app.get('/mcp', handleSessionRequest);
app.delete('/mcp', handleSessionRequest);

app.delete('/mcp/session', async (req, res) => {
  const sessionId = (req.headers['Mcp-Session-Id'] ??
    req.headers['mcp-session-id']) as string | undefined;

  if (!sessionId || !sessions.has(sessionId)) {
    console.log(`[Session] DELETE /mcp/session failed - session not found: ${sessionId || 'undefined'}`);
    res.status(404).json({
      jsonrpc: '2.0',
      error: {
        code: -32001,
        message: 'Session not found',
      },
    });
    return;
  }

  await deleteSession(sessionId);
  res.status(204).send();
});

app.get('/health', (req, res) => {
  res.status(200).send('OK');
});

app.listen(PORT);
console.log(`MCP server listening on port ${PORT}`);
console.log(`Session file: ${SESSION_FILE}`);
console.log(`Max sessions: ${MAX_SESSIONS}`);
console.log(`Cleanup session files on delete: ${CLEANUP_SESSION_FILES}`);
