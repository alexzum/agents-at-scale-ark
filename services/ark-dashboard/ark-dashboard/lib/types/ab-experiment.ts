export type ABExperimentStatus = 'pending' | 'running' | 'completed' | 'failed' | 'applied'

export type ABExperimentTargetType = 'agent' | 'team'

export type ABExperimentWinner = 'baseline' | 'experiment' | 'tie'

export interface ABExperimentTargetChanges {
  model?: string
  instructions?: string
}

export interface ABExperimentModifications {
  input?: string
  targetType?: ABExperimentTargetType
  targetName?: string
  targetChanges?: ABExperimentTargetChanges
}

export interface ABExperimentCriteriaScores {
  [criterion: string]: number
}

export interface ABExperimentVariantResults {
  overallScore: number
  criteria: ABExperimentCriteriaScores
  cost?: number
  latency?: number
}

export interface ABExperimentResults {
  baseline: ABExperimentVariantResults
  experiment: ABExperimentVariantResults
  winner: ABExperimentWinner
  improvement: number
}

export interface ABExperimentEvaluations {
  baseline: string[]
  experiment: string[]
}

export interface ABExperiment {
  id: string
  status: ABExperimentStatus
  createdAt: string
  createdBy?: string
  variantQuery: string
  variantAgent?: string
  modifications: ABExperimentModifications
  evaluations?: ABExperimentEvaluations
  results?: ABExperimentResults
  appliedAt?: string
  appliedWinner?: ABExperimentWinner
}

export interface ABExperimentAnnotation {
  'ab-experiment'?: string
}

export function parseABExperiment(annotation: string | undefined): ABExperiment | null {
  if (!annotation) return null

  try {
    const parsed = JSON.parse(annotation)
    return parsed as ABExperiment
  } catch (error) {
    console.error('Failed to parse ab-experiment annotation:', error)
    return null
  }
}

export function serializeABExperiment(experiment: ABExperiment): string {
  return JSON.stringify(experiment, null, 2)
}
