import { ArkEvaluation } from '../ArkEvaluation.node';
import { IExecuteFunctions, ILoadOptionsFunctions } from 'n8n-workflow';
import {
  createMockExecuteFunctions,
  createMockLoadOptionsFunctions,
} from '../../../test-helpers/mocks';
import {
  evaluatorsListFixture,
  directEvaluationFixture,
  queryEvaluationFixture,
} from '../../../test-helpers/fixtures';

describe('ArkEvaluation Node', () => {
  let arkEvaluation: ArkEvaluation;

  beforeEach(() => {
    arkEvaluation = new ArkEvaluation();
  });

  describe('Node Metadata', () => {
    it('should have correct displayName', () => {
      expect(arkEvaluation.description.displayName).toBe('ARK Evaluation');
    });

    it('should have correct name', () => {
      expect(arkEvaluation.description.name).toBe('arkEvaluation');
    });

    it('should have correct group', () => {
      expect(arkEvaluation.description.group).toEqual(['transform']);
    });

    it('should have correct version', () => {
      expect(arkEvaluation.description.version).toBe(1);
    });

    it('should have inputs and outputs', () => {
      expect(arkEvaluation.description.inputs).toEqual(['main']);
      expect(arkEvaluation.description.outputs).toEqual(['main']);
    });

    it('should require ARK API credentials', () => {
      expect(arkEvaluation.description.credentials).toEqual([
        {
          name: 'arkApi',
          required: true,
        },
      ]);
    });

    it('should have an icon', () => {
      expect(arkEvaluation.description.icon).toBe('file:ark-evaluation.svg');
    });
  });

  describe('Node Properties', () => {
    it('should have evaluation type property', () => {
      const typeProperty = arkEvaluation.description.properties.find(
        (p: any) => p.name === 'evaluationType'
      );

      expect(typeProperty).toBeDefined();
      expect(typeProperty?.displayName).toBe('Evaluation Type');
      expect(typeProperty?.type).toBe('options');
      expect(typeProperty?.default).toBe('direct');
    });

    it('should have evaluator property with dynamic options', () => {
      const evaluatorProperty = arkEvaluation.description.properties.find(
        (p: any) => p.name === 'evaluator'
      );

      expect(evaluatorProperty).toBeDefined();
      expect(evaluatorProperty?.displayName).toBe('Evaluator');
      expect(evaluatorProperty?.type).toBe('options');
      expect(evaluatorProperty?.typeOptions?.loadOptionsMethod).toBe('getEvaluators');
      expect(evaluatorProperty?.required).toBe(true);
    });

    it('should have input property for direct evaluation', () => {
      const inputProperty = arkEvaluation.description.properties.find(
        (p: any) => p.name === 'input'
      );

      expect(inputProperty).toBeDefined();
      expect(inputProperty?.displayName).toBe('Input');
      expect(inputProperty?.type).toBe('string');
    });

    it('should have output property for direct evaluation', () => {
      const outputProperty = arkEvaluation.description.properties.find(
        (p: any) => p.name === 'output'
      );

      expect(outputProperty).toBeDefined();
      expect(outputProperty?.displayName).toBe('Output');
      expect(outputProperty?.type).toBe('string');
    });

    it('should have queryName property for query evaluation', () => {
      const queryNameProperty = arkEvaluation.description.properties.find(
        (p: any) => p.name === 'queryName'
      );

      expect(queryNameProperty).toBeDefined();
      expect(queryNameProperty?.displayName).toBe('Query Name');
      expect(queryNameProperty?.type).toBe('string');
    });

    it('should have wait property', () => {
      const waitProperty = arkEvaluation.description.properties.find(
        (p: any) => p.name === 'wait'
      );

      expect(waitProperty).toBeDefined();
      expect(waitProperty?.displayName).toBe('Wait for Completion');
      expect(waitProperty?.type).toBe('boolean');
      expect(waitProperty?.default).toBe(true);
    });

    it('should have timeout property', () => {
      const timeoutProperty = arkEvaluation.description.properties.find(
        (p: any) => p.name === 'timeout'
      );

      expect(timeoutProperty).toBeDefined();
      expect(timeoutProperty?.displayName).toBe('Timeout');
      expect(timeoutProperty?.type).toBe('number');
      expect(timeoutProperty?.default).toBe(300);
    });
  });

  describe('getEvaluators() Loader Method', () => {
    it('should fetch and format evaluators list', async () => {
      const mockFunctions = createMockLoadOptionsFunctions();
      (mockFunctions.helpers!.request as jest.Mock).mockResolvedValue(evaluatorsListFixture);

      const result = await arkEvaluation.methods!.loadOptions!.getEvaluators!.call(
        mockFunctions as ILoadOptionsFunctions
      );

      expect(result).toHaveLength(2);
      expect(result[0]).toEqual({
        name: 'correctness-evaluator',
        value: 'correctness-evaluator',
      });
      expect(result[1]).toEqual({
        name: 'relevance-evaluator',
        value: 'relevance-evaluator',
      });
    });

    it('should handle fetch errors gracefully', async () => {
      const mockFunctions = createMockLoadOptionsFunctions();
      (mockFunctions.helpers!.request as jest.Mock).mockRejectedValue(
        new Error('API Error')
      );

      const result = await arkEvaluation.methods!.loadOptions!.getEvaluators!.call(
        mockFunctions as ILoadOptionsFunctions
      );

      expect(result).toEqual([]);
    });
  });
});
