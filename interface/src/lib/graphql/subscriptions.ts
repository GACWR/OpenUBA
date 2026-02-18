import { gql } from '@apollo/client';

export const ANOMALY_SUBSCRIPTION = gql`
  subscription OnAnomalyChanged {
    anomalyChanged {
      operation
      id
      entityId
      riskScore
    }
  }
`;

export const CASE_SUBSCRIPTION = gql`
  subscription OnCaseChanged {
    caseChanged {
      operation
      id
      title
      status
    }
  }
`;

export const EXECUTION_SUBSCRIPTION = gql`
  subscription OnExecutionChanged {
    executionChanged {
      operation
      id
      modelId
      status
    }
  }
`;

