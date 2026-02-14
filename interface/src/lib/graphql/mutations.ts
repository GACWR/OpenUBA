import { gql } from '@apollo/client';

// Model mutations
export const CREATE_MODEL = gql`
  mutation CreateModel($input: CreateModelInput!) {
    createModel(input: $input) {
      model {
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

export const UPDATE_MODEL = gql`
  mutation UpdateModel($id: UUID!, $input: UpdateModelInput!) {
    updateModelById(input: { id: $id, modelPatch: $input }) {
      model {
        id
        name
        version
        status
        enabled
        description
      }
    }
  }
`;

export const DELETE_MODEL = gql`
  mutation DeleteModel($id: UUID!) {
    deleteModelById(input: { id: $id }) {
      deletedModelId
    }
  }
`;

// Anomaly mutations
export const CREATE_ANOMALY = gql`
  mutation CreateAnomaly($input: CreateAnomalyInput!) {
    createAnomaly(input: $input) {
      anomaly {
        id
        entityId
        entityType
        riskScore
        anomalyType
        timestamp
        modelId
      }
    }
  }
`;

export const ACKNOWLEDGE_ANOMALY = gql`
  mutation AcknowledgeAnomaly($id: UUID!, $acknowledgedBy: String!) {
    updateAnomalyById(
      input: {
        id: $id
        anomalyPatch: {
          acknowledged: true
          acknowledgedBy: $acknowledgedBy
        }
      }
    ) {
      anomaly {
        id
        acknowledged
        acknowledgedBy
        acknowledgedAt
      }
    }
  }
`;

export const DELETE_ANOMALY = gql`
  mutation DeleteAnomaly($id: UUID!) {
    deleteAnomalyById(input: { id: $id }) {
      deletedAnomalyId
    }
  }
`;

// Case mutations
export const CREATE_CASE = gql`
  mutation CreateCase($input: CreateCaseInput!) {
    createCase(input: $input) {
      case {
        id
        title
        description
        status
        severity
        createdAt
      }
    }
  }
`;

export const UPDATE_CASE = gql`
  mutation UpdateCase($id: UUID!, $input: UpdateCaseInput!) {
    updateCaseById(input: { id: $id, casePatch: $input }) {
      case {
        id
        title
        description
        status
        severity
        updatedAt
      }
    }
  }
`;

export const DELETE_CASE = gql`
  mutation DeleteCase($id: UUID!) {
    deleteCaseById(input: { id: $id }) {
      deletedCaseId
    }
  }
`;

export const LINK_ANOMALY_TO_CASE = gql`
  mutation LinkAnomalyToCase($caseId: UUID!, $anomalyId: UUID!) {
    createCaseAnomaly(
      input: {
        caseAnomaly: {
          caseId: $caseId
          anomalyId: $anomalyId
        }
      }
    ) {
      caseAnomaly {
        caseId
        anomalyId
      }
    }
  }
`;

// Rule mutations
export const CREATE_RULE = gql`
  mutation CreateRule($input: CreateRuleInput!) {
    createRule(input: $input) {
      rule {
        id
        name
        description
        ruleType
        condition
        enabled
        score
        severity
        flowGraph
        createdAt
      }
    }
  }
`;

export const UPDATE_RULE = gql`
  mutation UpdateRule($id: UUID!, $patch: RulePatch!) {
    updateRuleById(input: { id: $id, rulePatch: $patch }) {
      rule {
        id
        name
        description
        ruleType
        condition
        enabled
        score
        severity
        flowGraph
        lastTriggeredAt
        updatedAt
      }
    }
  }
`;

export const DELETE_RULE = gql`
  mutation DeleteRule($id: UUID!) {
    deleteRuleById(input: { id: $id }) {
      deletedRuleId
    }
  }
`;

// Alert mutations
export const ACKNOWLEDGE_ALERT = gql`
  mutation AcknowledgeAlert($id: UUID!, $acknowledgedBy: String!) {
    updateAlertById(
      input: {
        id: $id
        alertPatch: {
          acknowledged: true
          acknowledgedBy: $acknowledgedBy
        }
      }
    ) {
      alert {
        id
        acknowledged
        acknowledgedBy
        acknowledgedAt
      }
    }
  }
`;

// Feedback mutations
export const CREATE_FEEDBACK = gql`
  mutation CreateFeedback($input: CreateFeedbackInput!) {
    createUserFeedback(input: $input) {
      userFeedback {
        id
        anomalyId
        feedbackType
        notes
        userId
        createdAt
      }
    }
  }
`;

