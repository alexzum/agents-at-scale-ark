import { describe, it, expect, jest, beforeEach, afterEach } from '@jest/globals';
import { createMemoryCommand } from './index.js';
import output from '../../lib/output.js';
import { ArkApiProxy } from '../../lib/arkApiProxy.js';

// Mock dependencies
jest.mock('../../lib/output.js', () => ({
  default: {
    info: jest.fn(),
    success: jest.fn(),
    error: jest.fn(),
  },
}));

jest.mock('../../lib/arkApiProxy.js', () => ({
  ArkApiProxy: jest.fn(),
}));

describe('Memory Command', () => {
  let mockArkApiProxy: any;
  let mockArkApiClient: any;
  let mockConfig: any;

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Setup mock API client
    mockArkApiClient = {
      getSessions: jest.fn(),
      deleteSession: jest.fn(),
      deleteQueryMessages: jest.fn(),
      deleteAllSessions: jest.fn(),
    };

    // Setup mock proxy
    mockArkApiProxy = {
      start: jest.fn(() => Promise.resolve(mockArkApiClient)),
      stop: jest.fn(),
    };

    (ArkApiProxy as any).mockImplementation(() => mockArkApiProxy);
    
    mockConfig = {};
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Command Structure', () => {
    it('should create memory command with correct structure', () => {
      const command = createMemoryCommand(mockConfig);
      
      expect(command.name()).toBe('memory');
      expect(command.alias()).toBe('mem');
      expect(command.description()).toBe('Manage memory sessions and queries');
    });

    it('should have list subcommand', () => {
      const command = createMemoryCommand(mockConfig);
      const subcommands = command.commands.map(cmd => cmd.name());
      
      expect(subcommands).toContain('list');
    });

    it('should have reset subcommand with nested commands', () => {
      const command = createMemoryCommand(mockConfig);
      const resetCommand = command.commands.find(cmd => cmd.name() === 'reset');
      
      expect(resetCommand).toBeDefined();
      expect(resetCommand?.description()).toBe('Reset/delete memory data');
      
      const resetSubcommands = resetCommand?.commands.map(cmd => cmd.name()) || [];
      expect(resetSubcommands).toContain('session');
      expect(resetSubcommands).toContain('query');
      expect(resetSubcommands).toContain('all');
    });
  });

  describe('List Sessions', () => {
    it('should list sessions successfully', async () => {
      const mockSessions = [
        { sessionId: 'session-1', memoryName: 'memory-1' },
        { sessionId: 'session-2', memoryName: 'memory-2' },
      ];
      
      mockArkApiClient.getSessions.mockResolvedValue(mockSessions);
      
      const command = createMemoryCommand(mockConfig);
      
      // Simulate command execution
      const listCommand = command.commands.find(cmd => cmd.name() === 'list');
      expect(listCommand).toBeDefined();
      
      // Test the function directly
      const { listSessions } = await import('./index.js');
      await listSessions({ output: 'text' });
      
      expect(mockArkApiClient.getSessions).toHaveBeenCalled();
      expect(output.info).toHaveBeenCalledWith('Sessions:');
      expect(output.info).toHaveBeenCalledWith('  session-1 (memory: memory-1)');
      expect(output.info).toHaveBeenCalledWith('  session-2 (memory: memory-2)');
      expect(mockArkApiProxy.stop).toHaveBeenCalled();
    });

    it('should handle empty sessions list', async () => {
      mockArkApiClient.getSessions.mockResolvedValue([]);
      
      const { listSessions } = await import('./index.js');
      await listSessions({ output: 'text' });
      
      expect(output.info).toHaveBeenCalledWith('No sessions found');
      expect(mockArkApiProxy.stop).toHaveBeenCalled();
    });

    it('should output JSON format when requested', async () => {
      const mockSessions = [{ sessionId: 'session-1', memoryName: 'memory-1' }];
      mockArkApiClient.getSessions.mockResolvedValue(mockSessions);
      
      const { listSessions } = await import('./index.js');
      await listSessions({ output: 'json' });
      
      expect(output.info).toHaveBeenCalledWith(JSON.stringify(mockSessions, null, 2));
      expect(mockArkApiProxy.stop).toHaveBeenCalled();
    });

    it('should handle errors gracefully', async () => {
      const error = new Error('API Error');
      mockArkApiClient.getSessions.mockRejectedValue(error);
      
      const { listSessions } = await import('./index.js');
      
      // Mock process.exit to prevent actual exit
      const mockExit = jest.spyOn(process, 'exit').mockImplementation(() => {
        throw new Error('process.exit called');
      });
      
      await expect(listSessions({ output: 'text' })).rejects.toThrow('process.exit called');
      
      expect(output.error).toHaveBeenCalledWith('Failed to list sessions:', error);
      expect(mockExit).toHaveBeenCalledWith(1);
      
      mockExit.mockRestore();
    });
  });

  describe('Reset Session', () => {
    it('should delete session successfully', async () => {
      const mockResponse = { message: 'Session deleted successfully' };
      mockArkApiClient.deleteSession.mockResolvedValue(mockResponse);
      
      const { resetSession } = await import('./index.js');
      await resetSession('session-123', { output: 'text' });
      
      expect(mockArkApiClient.deleteSession).toHaveBeenCalledWith('session-123');
      expect(output.success).toHaveBeenCalledWith('Session session-123 deleted successfully');
      expect(mockArkApiProxy.stop).toHaveBeenCalled();
    });

    it('should output JSON format when requested', async () => {
      const mockResponse = { message: 'Session deleted successfully' };
      mockArkApiClient.deleteSession.mockResolvedValue(mockResponse);
      
      const { resetSession } = await import('./index.js');
      await resetSession('session-123', { output: 'json' });
      
      expect(output.info).toHaveBeenCalledWith(JSON.stringify(mockResponse, null, 2));
      expect(mockArkApiProxy.stop).toHaveBeenCalled();
    });

    it('should handle errors gracefully', async () => {
      const error = new Error('Delete failed');
      mockArkApiClient.deleteSession.mockRejectedValue(error);
      
      const { resetSession } = await import('./index.js');
      
      const mockExit = jest.spyOn(process, 'exit').mockImplementation(() => {
        throw new Error('process.exit called');
      });
      
      await expect(resetSession('session-123', { output: 'text' })).rejects.toThrow('process.exit called');
      
      expect(output.error).toHaveBeenCalledWith('Failed to delete session session-123:', error);
      expect(mockExit).toHaveBeenCalledWith(1);
      
      mockExit.mockRestore();
    });
  });

  describe('Reset Query', () => {
    it('should delete query messages successfully', async () => {
      const mockResponse = { message: 'Query messages deleted successfully' };
      mockArkApiClient.deleteQueryMessages.mockResolvedValue(mockResponse);
      
      const { resetQuery } = await import('./index.js');
      await resetQuery('session-123', 'query-456', { output: 'text' });
      
      expect(mockArkApiClient.deleteQueryMessages).toHaveBeenCalledWith('session-123', 'query-456');
      expect(output.success).toHaveBeenCalledWith('Query query-456 messages deleted successfully from session session-123');
      expect(mockArkApiProxy.stop).toHaveBeenCalled();
    });

    it('should output JSON format when requested', async () => {
      const mockResponse = { message: 'Query messages deleted successfully' };
      mockArkApiClient.deleteQueryMessages.mockResolvedValue(mockResponse);
      
      const { resetQuery } = await import('./index.js');
      await resetQuery('session-123', 'query-456', { output: 'json' });
      
      expect(output.info).toHaveBeenCalledWith(JSON.stringify(mockResponse, null, 2));
      expect(mockArkApiProxy.stop).toHaveBeenCalled();
    });

    it('should handle errors gracefully', async () => {
      const error = new Error('Delete failed');
      mockArkApiClient.deleteQueryMessages.mockRejectedValue(error);
      
      const { resetQuery } = await import('./index.js');
      
      const mockExit = jest.spyOn(process, 'exit').mockImplementation(() => {
        throw new Error('process.exit called');
      });
      
      await expect(resetQuery('session-123', 'query-456', { output: 'text' })).rejects.toThrow('process.exit called');
      
      expect(output.error).toHaveBeenCalledWith('Failed to delete query query-456 messages:', error);
      expect(mockExit).toHaveBeenCalledWith(1);
      
      mockExit.mockRestore();
    });
  });

  describe('Reset All', () => {
    it('should delete all sessions successfully', async () => {
      const mockResponse = { message: 'All sessions deleted successfully' };
      mockArkApiClient.deleteAllSessions.mockResolvedValue(mockResponse);
      
      const { resetAll } = await import('./index.js');
      await resetAll({ output: 'text' });
      
      expect(mockArkApiClient.deleteAllSessions).toHaveBeenCalled();
      expect(output.success).toHaveBeenCalledWith('All sessions deleted successfully');
      expect(mockArkApiProxy.stop).toHaveBeenCalled();
    });

    it('should output JSON format when requested', async () => {
      const mockResponse = { message: 'All sessions deleted successfully' };
      mockArkApiClient.deleteAllSessions.mockResolvedValue(mockResponse);
      
      const { resetAll } = await import('./index.js');
      await resetAll({ output: 'json' });
      
      expect(output.info).toHaveBeenCalledWith(JSON.stringify(mockResponse, null, 2));
      expect(mockArkApiProxy.stop).toHaveBeenCalled();
    });

    it('should handle errors gracefully', async () => {
      const error = new Error('Delete all failed');
      mockArkApiClient.deleteAllSessions.mockRejectedValue(error);
      
      const { resetAll } = await import('./index.js');
      
      const mockExit = jest.spyOn(process, 'exit').mockImplementation(() => {
        throw new Error('process.exit called');
      });
      
      await expect(resetAll({ output: 'text' })).rejects.toThrow('process.exit called');
      
      expect(output.error).toHaveBeenCalledWith('Failed to delete all sessions:', error);
      expect(mockExit).toHaveBeenCalledWith(1);
      
      mockExit.mockRestore();
    });
  });

  describe('Default Action', () => {
    it('should default to listing sessions when no subcommand provided', async () => {
      const mockSessions = [{ sessionId: 'session-1', memoryName: 'memory-1' }];
      mockArkApiClient.getSessions.mockResolvedValue(mockSessions);
      
      // Test the default action
      const { listSessions } = await import('./index.js');
      await listSessions({ output: 'text' });
      
      expect(mockArkApiClient.getSessions).toHaveBeenCalled();
      expect(output.info).toHaveBeenCalledWith('Sessions:');
    });
  });
});
