import { gql } from '@apollo/client';

export const GET_MODELS = gql`
  query GetModels {
    allModels(first: 200) {
      totalCount
      nodes {
        id
        name
        version
        status
        sourceType
        enabled
        description
        author
        createdAt
      }
    }
  }
`;

export const GET_MODEL = gql`
  query GetModel($id: UUID!) {
    modelById(id: $id) {
      id
      name
      version
      status
      sourceType
      enabled
      description
      author
      manifest
      createdAt
    }
  }
`;

export const GET_ANOMALIES = gql`
  query GetAnomalies {
    allAnomalies(orderBy: TIMESTAMP_DESC, first: 500) {
      totalCount
      nodes {
        id
        entityId
        entityType
        riskScore
        anomalyType
        timestamp
        acknowledged
        acknowledgedAt
        acknowledgedBy
        modelId
        modelByModelId {
          name
          version
        }
        details
        createdAt
      }
    }
  }
`;

export const GET_CASES = gql`
  query GetCases {
    allCases(orderBy: CREATED_AT_DESC, first: 200) {
      totalCount
      nodes {
        id
        title
        status
        severity
        description
        assignedTo
        analystNotes
        createdAt
        updatedAt
        resolvedAt
        caseAnomaliesByCaseId {
          nodes {
            anomalyByAnomalyId {
              id
              entityId
              entityType
              riskScore
              anomalyType
              timestamp
              acknowledged
            }
          }
        }
      }
    }
  }
`;

export const GET_RULES = gql`
  query GetRules {
    allRules(first: 200) {
      totalCount
      nodes {
        id
        name
        description
        ruleType
        condition
        features
        score
        enabled
        severity
        flowGraph
        lastTriggeredAt
        createdAt
        updatedAt
      }
    }
  }
`;

export const GET_ALERTS = gql`
  query GetAlerts {
    allAlerts(orderBy: CREATED_AT_DESC, first: 500) {
      totalCount
      nodes {
        id
        ruleId
        severity
        message
        entityId
        entityType
        context
        acknowledged
        acknowledgedAt
        acknowledgedBy
        createdAt
        ruleByRuleId {
          name
        }
      }
    }
  }
`;


export const GET_EXECUTION_LOGS = gql`
  query GetExecutionLogs {
    allExecutionLogs(orderBy: STARTED_AT_DESC, first: 200) {
      totalCount
      nodes {
        id
        modelId
        status
        startedAt
        completedAt
        executionTimeSeconds
        executionTimeSeconds
        errorMessage
        outputSummary
        modelByModelId {
          name
        }
      }
    }
  }
`;

export const GET_MODEL_RUNS = gql`
  query GetModelRuns {
    allModelRuns(orderBy: CREATED_AT_DESC, first: 200) {
      totalCount
      nodes {
        id
        runType
        status
        startedAt
        finishedAt
        errorMessage
        resultSummary
        modelVersionByModelVersionId {
          version
          modelByModelId {
            id
            name
          }
        }
        errorLogs: modelLogsByModelRunId(condition: { level: "error" }) {
          totalCount
        }
        warningLogs: modelLogsByModelRunId(condition: { level: "warning" }) {
          totalCount
        }
      }
    }
  }
`;

export const GET_ENTITIES = gql`
  query GetEntities {
    allEntities(orderBy: RISK_SCORE_DESC, first: 500) {
      totalCount
      nodes {
        id
        entityId
        entityType
        displayName
        riskScore
        anomalyCount
        firstSeen
        lastSeen
        metadata
        createdAt
      }
    }
  }
`;

export const GET_MODEL_LOGS = gql`
  query GetModelLogs($runId: UUID!) {
    allModelLogs(condition: { modelRunId: $runId }, orderBy: CREATED_AT_ASC, first: 1000) {
      totalCount
      nodes {
        id
        level
        message
        loggerName
        createdAt
      }
    }
  }
`;
