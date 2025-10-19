import { describe, it, expect, jest, beforeEach, afterEach } from '@jest/globals';
import { ArkApiClient } from './arkApiClient.js';

// Mock fetch globally
(globalThis as any).fetch = jest.fn();

describe('ArkApiClient Delete Methods', () => {
  let client: ArkApiClient;
  let mockFetch: any;

  beforeEach(() => {
    client = new ArkApiClient('http://localhost:8080');
    mockFetch = jest.mocked(fetch);
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('deleteSession', () => {
    it('should delete session successfully', async () => {
      const mockResponse = { message: 'Session deleted successfully' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await client.deleteSession('session-123');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8080/v1/sessions/session-123',
        {
          method: 'DELETE'
        }
      );
      expect(result).toEqual(mockResponse);
    });

    it('should handle HTTP error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
      });

      await expect(client.deleteSession('nonexistent-session')).rejects.toThrow(
        'Failed to delete session: HTTP error! status: 404'
      );
    });

    it('should handle network error', async () => {
      const networkError = new Error('Network error');
      mockFetch.mockRejectedValueOnce(networkError);

      await expect(client.deleteSession('session-123')).rejects.toThrow(
        'Failed to delete session: Network error'
      );
    });

    it('should handle JSON parsing error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.reject(new Error('Invalid JSON')),
      });

      await expect(client.deleteSession('session-123')).rejects.toThrow(
        'Failed to delete session: Invalid JSON'
      );
    });
  });

  describe('deleteQueryMessages', () => {
    it('should delete query messages successfully', async () => {
      const mockResponse = { message: 'Query messages deleted successfully' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await client.deleteQueryMessages('session-123', 'query-456');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8080/v1/sessions/session-123/queries/query-456/messages',
        {
          method: 'DELETE'
        }
      );
      expect(result).toEqual(mockResponse);
    });

    it('should handle HTTP error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      await expect(client.deleteQueryMessages('session-123', 'query-456')).rejects.toThrow(
        'Failed to delete query messages: HTTP error! status: 500'
      );
    });

    it('should handle network error', async () => {
      const networkError = new Error('Connection timeout');
      mockFetch.mockRejectedValueOnce(networkError);

      await expect(client.deleteQueryMessages('session-123', 'query-456')).rejects.toThrow(
        'Failed to delete query messages: Connection timeout'
      );
    });
  });

  describe('deleteAllSessions', () => {
    it('should delete all sessions successfully', async () => {
      const mockResponse = { message: 'All sessions deleted successfully' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await client.deleteAllSessions();

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8080/v1/sessions',
        {
          method: 'DELETE'
        }
      );
      expect(result).toEqual(mockResponse);
    });

    it('should handle HTTP error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
      });

      await expect(client.deleteAllSessions()).rejects.toThrow(
        'Failed to delete all sessions: HTTP error! status: 403'
      );
    });

    it('should handle network error', async () => {
      const networkError = new Error('DNS resolution failed');
      mockFetch.mockRejectedValueOnce(networkError);

      await expect(client.deleteAllSessions()).rejects.toThrow(
        'Failed to delete all sessions: DNS resolution failed'
      );
    });
  });

  describe('getSessions', () => {
    it('should get sessions successfully', async () => {
      const mockSessions = [
        { sessionId: 'session-1', memoryName: 'memory-1' },
        { sessionId: 'session-2', memoryName: 'memory-2' },
      ];
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockSessions),
      });

      const result = await client.getSessions();

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8080/v1/sessions',
        {
          method: 'GET'
        }
      );
      expect(result).toEqual(mockSessions);
    });

    it('should handle empty sessions list', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([]),
      });

      const result = await client.getSessions();

      expect(result).toEqual([]);
    });

    it('should handle HTTP error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
      });

      await expect(client.getSessions()).rejects.toThrow(
        'Failed to get sessions: HTTP error! status: 401'
      );
    });

    it('should handle network error', async () => {
      const networkError = new Error('Connection refused');
      mockFetch.mockRejectedValueOnce(networkError);

      await expect(client.getSessions()).rejects.toThrow(
        'Failed to get sessions: Connection refused'
      );
    });
  });

  describe('Error Handling', () => {
    it('should handle unknown error types', async () => {
      mockFetch.mockRejectedValueOnce('Unknown error');

      await expect(client.deleteSession('session-123')).rejects.toThrow(
        'Failed to delete session: Unknown error'
      );
    });

    it('should handle null error', async () => {
      mockFetch.mockRejectedValueOnce(null);

      await expect(client.deleteSession('session-123')).rejects.toThrow(
        'Failed to delete session: Unknown error'
      );
    });

    it('should handle undefined error', async () => {
      mockFetch.mockRejectedValueOnce(undefined);

      await expect(client.deleteSession('session-123')).rejects.toThrow(
        'Failed to delete session: Unknown error'
      );
    });
  });

  describe('URL Construction', () => {
    it('should construct correct URLs for different base URLs', async () => {
      const clientWithCustomUrl = new ArkApiClient('https://api.example.com:9000');
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });

      await clientWithCustomUrl.deleteSession('test-session');

      expect(mockFetch).toHaveBeenCalledWith(
        'https://api.example.com:9000/v1/sessions/test-session',
        {
          method: 'DELETE'
        }
      );
    });

    it('should handle base URL with trailing slash', async () => {
      const clientWithTrailingSlash = new ArkApiClient('http://localhost:8080/');
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });

      await clientWithTrailingSlash.deleteSession('test-session');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8080/v1/sessions/test-session',
        {
          method: 'DELETE'
        }
      );
    });
  });
});
