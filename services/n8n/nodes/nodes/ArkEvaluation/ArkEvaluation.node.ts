import {
  IExecuteFunctions,
  ILoadOptionsFunctions,
  INodeExecutionData,
  INodePropertyOptions,
  INodeType,
  INodeTypeDescription,
} from 'n8n-workflow';

export class ArkEvaluation implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'ARK Evaluation',
    name: 'arkEvaluation',
    icon: 'file:ark-evaluation.svg',
    group: ['transform'],
    version: 1,
    description: 'Create and execute ARK evaluations',
    defaults: {
      name: 'ARK Evaluation',
    },
    inputs: ['main'],
    outputs: ['main'],
    credentials: [
      {
        name: 'arkApi',
        required: true,
      },
    ],
    properties: [
      {
        displayName: 'Evaluation Type',
        name: 'evaluationType',
        type: 'options',
        options: [
          {
            name: 'Direct',
            value: 'direct',
            description: 'Evaluate input/output directly',
          },
          {
            name: 'Query',
            value: 'query',
            description: 'Evaluate based on existing query',
          },
        ],
        default: 'direct',
        description: 'Type of evaluation to perform',
      },
      {
        displayName: 'Evaluator',
        name: 'evaluator',
        type: 'options',
        typeOptions: {
          loadOptionsMethod: 'getEvaluators',
        },
        default: '',
        required: true,
        description: 'The evaluator to use',
      },
      {
        displayName: 'Input',
        name: 'input',
        type: 'string',
        typeOptions: {
          rows: 4,
        },
        displayOptions: {
          show: {
            evaluationType: ['direct'],
          },
        },
        default: '',
        required: true,
        description: 'The input to evaluate',
      },
      {
        displayName: 'Output',
        name: 'output',
        type: 'string',
        typeOptions: {
          rows: 4,
        },
        displayOptions: {
          show: {
            evaluationType: ['direct'],
          },
        },
        default: '',
        required: true,
        description: 'The output to evaluate',
      },
      {
        displayName: 'Query Name',
        name: 'queryName',
        type: 'string',
        displayOptions: {
          show: {
            evaluationType: ['query'],
          },
        },
        default: '',
        required: true,
        description: 'Name of the query to evaluate',
      },
      {
        displayName: 'Response Target',
        name: 'responseTarget',
        type: 'options',
        options: [
          {
            name: 'Final',
            value: 'final',
            description: 'Evaluate final response',
          },
          {
            name: 'Intermediate',
            value: 'intermediate',
            description: 'Evaluate intermediate steps',
          },
        ],
        displayOptions: {
          show: {
            evaluationType: ['query'],
          },
        },
        default: 'final',
        description: 'Which response to evaluate',
      },
      {
        displayName: 'Wait for Completion',
        name: 'wait',
        type: 'boolean',
        default: true,
        description: 'Whether to wait for evaluation to complete',
      },
      {
        displayName: 'Timeout',
        name: 'timeout',
        type: 'number',
        default: 300,
        displayOptions: {
          show: {
            wait: [true],
          },
        },
        description: 'Maximum time to wait for completion (seconds)',
      },
    ],
  };

  methods = {
    loadOptions: {
      async getEvaluators(this: ILoadOptionsFunctions): Promise<INodePropertyOptions[]> {
        const credentials = await this.getCredentials('arkApi');
        const baseUrl = credentials.baseUrl as string;

        try {
          const response = await this.helpers.request({
            method: 'GET',
            url: `${baseUrl}/v1/evaluators`,
            json: true,
          });

          return response.items.map((evaluator: any) => ({
            name: evaluator.name,
            value: evaluator.name,
          }));
        } catch (error) {
          return [];
        }
      },
    },
  };

  async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
    const items = this.getInputData();
    const returnData: INodeExecutionData[] = [];
    const credentials = await this.getCredentials('arkApi');
    const baseUrl = credentials.baseUrl as string;
    const token = credentials.token as string;

    for (let i = 0; i < items.length; i++) {
      const evaluationType = this.getNodeParameter('evaluationType', i) as string;
      const evaluator = this.getNodeParameter('evaluator', i) as string;
      const wait = this.getNodeParameter('wait', i) as boolean;
      const timeout = this.getNodeParameter('timeout', i, 300) as number;

      const evaluationName = `eval-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

      const requestBody: any = {
        name: evaluationName,
        type: evaluationType,
        evaluator: {
          name: evaluator,
        },
        config: {},
        timeout: `${timeout}s`,
      };

      if (evaluationType === 'direct') {
        const input = this.getNodeParameter('input', i) as string;
        const output = this.getNodeParameter('output', i) as string;
        requestBody.config.input = input;
        requestBody.config.output = output;
      } else if (evaluationType === 'query') {
        const queryName = this.getNodeParameter('queryName', i) as string;
        const responseTarget = this.getNodeParameter('responseTarget', i) as string;
        requestBody.config.queryRef = {
          name: queryName,
          responseTarget,
        };
      }

      const headers: any = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await this.helpers.request({
        method: 'POST',
        url: `${baseUrl}/v1/evaluations`,
        body: requestBody,
        headers,
        json: true,
      });

      if (wait) {
        const evaluationName = response.name;
        const startTime = Date.now();
        const maxWaitTime = timeout * 1000;

        while (true) {
          const statusResponse = await this.helpers.request({
            method: 'GET',
            url: `${baseUrl}/v1/evaluations/${evaluationName}`,
            headers,
            json: true,
          });

          const phase = statusResponse.status?.phase;

          if (phase === 'done' || phase === 'failed' || phase === 'error') {
            returnData.push({ json: statusResponse });
            break;
          }

          if (Date.now() - startTime > maxWaitTime) {
            throw new Error(`Evaluation timed out after ${timeout} seconds`);
          }

          await new Promise((resolve) => setTimeout(resolve, 2000));
        }
      } else {
        returnData.push({ json: response });
      }
    }

    return [returnData];
  }
}
