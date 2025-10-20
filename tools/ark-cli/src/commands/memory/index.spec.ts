import { describe, it, expect, jest, beforeEach, afterEach } from '@jest/globals';
import { createMemoryCommand } from './index.js';

// Mock dependencies
jest.mock('../../lib/output.js', () => ({
  default: {
    info: jest.fn(),
    success: jest.fn(),
    error: jest.fn(),
  },
}));

// Mock ArkApiProxy with a simpler approach
jest.mock('../../lib/arkApiProxy.js', () => {
  return {
    ArkApiProxy: jest.fn().mockImplementation(() => ({
      start: jest.fn(),
      stop: jest.fn(),
    })),
  };
});

describe('Memory Command', () => {
  let mockConfig: any;

  beforeEach(() => {
    jest.clearAllMocks();
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

  describe('Command Creation', () => {
    it('should create command without errors', () => {
      expect(() => createMemoryCommand(mockConfig)).not.toThrow();
    });

    it('should return a command object', () => {
      const command = createMemoryCommand(mockConfig);
      expect(command).toBeDefined();
      expect(typeof command.name).toBe('function');
      expect(typeof command.description).toBe('function');
    });
  });
});