"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArkEvaluation = void 0;
class ArkEvaluation {
    constructor() {
        this.description = {
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
        this.methods = {
            loadOptions: {
                async getEvaluators() {
                    const credentials = await this.getCredentials('arkApi');
                    const baseUrl = credentials.baseUrl;
                    try {
                        const response = await this.helpers.request({
                            method: 'GET',
                            url: `${baseUrl}/v1/evaluators`,
                            json: true,
                        });
                        return response.items.map((evaluator) => ({
                            name: evaluator.name,
                            value: evaluator.name,
                        }));
                    }
                    catch (error) {
                        return [];
                    }
                },
            },
        };
    }
    async execute() {
        var _a;
        const items = this.getInputData();
        const returnData = [];
        const credentials = await this.getCredentials('arkApi');
        const baseUrl = credentials.baseUrl;
        const token = credentials.token;
        for (let i = 0; i < items.length; i++) {
            const evaluationType = this.getNodeParameter('evaluationType', i);
            const evaluator = this.getNodeParameter('evaluator', i);
            const wait = this.getNodeParameter('wait', i);
            const timeout = this.getNodeParameter('timeout', i, 300);
            const evaluationName = `eval-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
            const requestBody = {
                name: evaluationName,
                type: evaluationType,
                evaluator: {
                    name: evaluator,
                },
                config: {},
                timeout: `${timeout}s`,
            };
            if (evaluationType === 'direct') {
                const input = this.getNodeParameter('input', i);
                const output = this.getNodeParameter('output', i);
                requestBody.config.input = input;
                requestBody.config.output = output;
            }
            else if (evaluationType === 'query') {
                const queryName = this.getNodeParameter('queryName', i);
                const responseTarget = this.getNodeParameter('responseTarget', i);
                requestBody.config.queryRef = {
                    name: queryName,
                    responseTarget,
                };
            }
            const headers = {
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
                    const phase = (_a = statusResponse.status) === null || _a === void 0 ? void 0 : _a.phase;
                    if (phase === 'done' || phase === 'failed' || phase === 'error') {
                        returnData.push({ json: statusResponse });
                        break;
                    }
                    if (Date.now() - startTime > maxWaitTime) {
                        throw new Error(`Evaluation timed out after ${timeout} seconds`);
                    }
                    await new Promise((resolve) => setTimeout(resolve, 2000));
                }
            }
            else {
                returnData.push({ json: response });
            }
        }
        return [returnData];
    }
}
exports.ArkEvaluation = ArkEvaluation;
//# sourceMappingURL=ArkEvaluation.node.js.map