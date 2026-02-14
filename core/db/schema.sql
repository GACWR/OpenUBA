-- OpenUBA v0.0.2 PostgreSQL Schema
-- This schema defines all tables for the OpenUBA platform

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Models table: stores model registry entries
CREATE TABLE models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug TEXT UNIQUE NOT NULL, -- stable id like 'model_tf_protobuf'
    name VARCHAR(255) NOT NULL,
    display_name TEXT,
    version VARCHAR(50) NOT NULL,
    source_type VARCHAR(50) NOT NULL, -- 'openuba_hub', 'github', 'huggingface', 'kubeflow', 'local_fs'
    source_url TEXT,
    manifest JSONB, -- full model manifest as json
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'installed', 'active', 'disabled'
    enabled BOOLEAN DEFAULT true,
    description TEXT,
    author VARCHAR(255),
    framework TEXT, -- 'sklearn', 'tensorflow', 'pytorch', 'spark_mllib', 'networkx_graph', etc.
    runtime VARCHAR(50) DEFAULT 'python-base', -- 'python-base', 'python-data'
    interface_version INT DEFAULT 1, -- 1 = legacy execute-only, 2 = new train/infer API
    default_version_id UUID, -- FK added via ALTER TABLE later
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, version)
);

CREATE INDEX idx_models_name ON models(name);
CREATE INDEX idx_models_status ON models(status);
CREATE INDEX idx_models_source_type ON models(source_type);

-- Model versions table: tracks version history
CREATE TABLE model_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL,
    source_uri TEXT, -- canonical URI (github://org/repo@sha:path/to/spec.json, openuba-hub://..., etc.)
    code_backend TEXT, -- 'local_fs', 'github', 'openuba_hub', etc.
    weights_backend TEXT, -- 'huggingface', 'local_fs', etc.
    manifest JSONB,
    status TEXT DEFAULT 'registered', -- 'registered', 'installed', 'trained', 'disabled'
    code_path TEXT, -- absolute path inside OpenUBA FS (/models/<slug>/<version>/) or mount path
    requirements TEXT, -- copy of requirements.txt if provided
    encoding_hash TEXT, -- hash of encoded model bundle (v1 data_hash)
    file_hash TEXT, -- hash of unpacked files (v1 file_hash)
    installed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model_id, version)
);

CREATE INDEX idx_model_versions_model_id ON model_versions(model_id);
CREATE INDEX idx_model_versions_status ON model_versions(status);

-- Model artifacts table: stores trained artifacts/checkpoints
CREATE TABLE model_artifacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_version_id UUID NOT NULL REFERENCES model_versions(id) ON DELETE CASCADE,
    kind TEXT NOT NULL, -- 'checkpoint', 'encoder', 'baseline', etc.
    format TEXT NOT NULL, -- 'sklearn_pickle', 'torch_pt', 'tf_saved_model', 'joblib', 'custom'
    path TEXT NOT NULL, -- path in storage/saved_models or external URI
    metrics JSONB, -- training metrics summary if applicable
    file_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_model_artifacts_model_version_id ON model_artifacts(model_version_id);
CREATE INDEX idx_model_artifacts_kind ON model_artifacts(kind);

-- Model runs table: tracks training and inference runs
CREATE TABLE model_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_version_id UUID NOT NULL REFERENCES model_versions(id) ON DELETE CASCADE,
    artifact_id UUID REFERENCES model_artifacts(id) ON DELETE SET NULL, -- set on successful training that writes an artifact
    run_type TEXT NOT NULL, -- 'train' | 'infer'
    status TEXT NOT NULL, -- 'pending', 'dispatched', 'running', 'succeeded', 'failed'
    data_loader_type TEXT, -- value from ModelDataLoader enum (LOCAL_PANDAS_CSV, ES_GENERIC, etc.)
    data_loader_context JSONB, -- same context schema as current models.json
    params JSONB, -- hyperparams, thresholds, etc.
    result_summary JSONB, -- e.g. number of anomalies, loss values
    error_message TEXT,
    k8s_job_name TEXT, -- k8s job name if applicable
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_model_runs_model_version_id ON model_runs(model_version_id);
CREATE INDEX idx_model_runs_status ON model_runs(status);
CREATE INDEX idx_model_runs_run_type ON model_runs(run_type);
CREATE INDEX idx_model_runs_artifact_id ON model_runs(artifact_id);

-- Model components table: stores individual model files with hashes
CREATE TABLE model_components (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    component_type VARCHAR(50) NOT NULL, -- 'external', 'internal', etc.
    file_hash VARCHAR(64) NOT NULL, -- sha256 hex
    data_hash VARCHAR(64), -- sha256 hex of data payload if applicable
    file_path TEXT, -- path where file is stored
    file_size BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model_id, filename)
);

CREATE INDEX idx_model_components_model_id ON model_components(model_id);
CREATE INDEX idx_model_components_file_hash ON model_components(file_hash);

-- Anomalies table: stores anomaly detection results
CREATE TABLE anomalies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE SET NULL,
    entity_id VARCHAR(255), -- user id or entity identifier
    entity_type VARCHAR(50) DEFAULT 'user', -- 'user', 'device', 'ip', etc.
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    risk_score DECIMAL(10, 2),
    anomaly_type VARCHAR(100),
    details JSONB, -- flexible json for anomaly-specific data
    acknowledged BOOLEAN DEFAULT false,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_anomalies_model_id ON anomalies(model_id);
CREATE INDEX idx_anomalies_entity_id ON anomalies(entity_id);
CREATE INDEX idx_anomalies_timestamp ON anomalies(timestamp);
CREATE INDEX idx_anomalies_risk_score ON anomalies(risk_score);
CREATE INDEX idx_anomalies_acknowledged ON anomalies(acknowledged);

-- Add run_id to anomalies so we can identify which run produced each anomaly
ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS run_id UUID REFERENCES model_runs(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_anomalies_run_id ON anomalies(run_id);

-- Entities table: registry of discovered entities (users, devices, IPs, servers)
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50) NOT NULL DEFAULT 'user',  -- 'user', 'device', 'ip', 'server', 'other'
    display_name VARCHAR(255),
    risk_score DECIMAL(10, 2) DEFAULT 0,              -- highest risk score seen
    anomaly_count INTEGER DEFAULT 0,
    first_seen TIMESTAMP WITH TIME ZONE,
    last_seen TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(entity_id, entity_type)
);

CREATE INDEX idx_entities_entity_id ON entities(entity_id);
CREATE INDEX idx_entities_entity_type ON entities(entity_type);
CREATE INDEX idx_entities_risk_score ON entities(risk_score);
CREATE INDEX idx_entities_last_seen ON entities(last_seen);

-- Cases table: security cases/incidents
CREATE TABLE cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'open', -- 'open', 'investigating', 'resolved', 'closed'
    severity VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    analyst_notes TEXT,
    assigned_to VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_severity ON cases(severity);
CREATE INDEX idx_cases_created_at ON cases(created_at);

-- Case-anomaly linking table (many-to-many)
CREATE TABLE case_anomalies (
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    anomaly_id UUID NOT NULL REFERENCES anomalies(id) ON DELETE CASCADE,
    PRIMARY KEY (case_id, anomaly_id)
);

CREATE INDEX idx_case_anomalies_case_id ON case_anomalies(case_id);
CREATE INDEX idx_case_anomalies_anomaly_id ON case_anomalies(anomaly_id);

-- Rules table: rule-based detection rules
CREATE TABLE rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rule_type VARCHAR(50) NOT NULL, -- 'single-fire', 'deviation', etc.
    condition TEXT NOT NULL, -- rule logic/condition
    features TEXT, -- comma-separated feature names
    score INTEGER DEFAULT 0,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rules_enabled ON rules(enabled);
CREATE INDEX idx_rules_rule_type ON rules(rule_type);

-- Add new columns to rules table for flow-based rules
ALTER TABLE rules ADD COLUMN IF NOT EXISTS severity VARCHAR(20) DEFAULT 'medium';
ALTER TABLE rules ADD COLUMN IF NOT EXISTS flow_graph JSONB;
ALTER TABLE rules ADD COLUMN IF NOT EXISTS last_triggered_at TIMESTAMP WITH TIME ZONE;

-- Alerts table: fired when a rule triggers
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id UUID NOT NULL REFERENCES rules(id) ON DELETE CASCADE,
    severity VARCHAR(20) NOT NULL DEFAULT 'medium',
    message TEXT NOT NULL,
    entity_id VARCHAR(255),
    entity_type VARCHAR(50) DEFAULT 'user',
    context JSONB,
    acknowledged BOOLEAN DEFAULT false,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alerts_rule_id ON alerts(rule_id);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_created_at ON alerts(created_at);
CREATE INDEX idx_alerts_acknowledged ON alerts(acknowledged);

-- Execution logs table: records of model execution runs
CREATE TABLE execution_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL, -- 'pending', 'running', 'completed', 'failed'
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    error_traceback TEXT,
    execution_time_seconds DECIMAL(10, 3),
    container_id VARCHAR(255), -- docker container id or k8s job name
    resource_usage JSONB, -- cpu, memory usage if available
    output_summary JSONB -- summary of results/output
);

CREATE INDEX idx_execution_logs_model_id ON execution_logs(model_id);
CREATE INDEX idx_execution_logs_status ON execution_logs(status);
CREATE INDEX idx_execution_logs_started_at ON execution_logs(started_at);

-- Model logs table: granular log entries from model execution
CREATE TABLE model_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_run_id UUID NOT NULL REFERENCES model_runs(id) ON DELETE CASCADE,
    level VARCHAR(20) NOT NULL,        -- 'info', 'warning', 'error'
    message TEXT NOT NULL,
    logger_name VARCHAR(255),          -- e.g. 'model_sklearn', 'runner'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_model_logs_run_id ON model_logs(model_run_id);
CREATE INDEX idx_model_logs_created_at ON model_logs(created_at);

-- User feedback table: feedback on anomalies for model learning
CREATE TABLE user_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    anomaly_id UUID NOT NULL REFERENCES anomalies(id) ON DELETE CASCADE,
    feedback_type VARCHAR(50) NOT NULL, -- 'true_positive', 'false_positive', 'needs_review'
    notes TEXT,
    user_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_feedback_anomaly_id ON user_feedback(anomaly_id);
CREATE INDEX idx_user_feedback_feedback_type ON user_feedback(feedback_type);

-- Users table: system users (if multi-user support needed)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'analyst', -- 'admin', 'analyst', 'viewer'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);

-- Audit log table: tracks all important actions
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action_type VARCHAR(100) NOT NULL, -- 'model_install', 'model_execute', 'case_create', etc.
    entity_type VARCHAR(50), -- 'model', 'anomaly', 'case', etc.
    entity_id UUID,
    user_id VARCHAR(255),
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_action_type ON audit_logs(action_type);
CREATE INDEX idx_audit_logs_entity_type ON audit_logs(entity_type);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- Data Ingestion Runs table: tracks data ingestion execution history
CREATE TABLE data_ingestion_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dataset_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'running', 'completed', 'failed'
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    details JSONB, -- summary of what was ingested (row counts, etc.)
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_data_ingestion_runs_status ON data_ingestion_runs(status);
CREATE INDEX idx_data_ingestion_runs_created_at ON data_ingestion_runs(created_at);

CREATE TRIGGER update_data_ingestion_runs_updated_at BEFORE UPDATE ON data_ingestion_runs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function to auto-populate entities from anomalies
CREATE OR REPLACE FUNCTION upsert_entity_on_anomaly()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.entity_id IS NOT NULL THEN
        INSERT INTO entities (entity_id, entity_type, risk_score, anomaly_count, first_seen, last_seen)
        VALUES (NEW.entity_id, COALESCE(NEW.entity_type, 'user'), COALESCE(NEW.risk_score, 0), 1, NEW.timestamp, NEW.timestamp)
        ON CONFLICT (entity_id, entity_type)
        DO UPDATE SET
            risk_score = GREATEST(entities.risk_score, COALESCE(NEW.risk_score, 0)),
            anomaly_count = entities.anomaly_count + 1,
            last_seen = GREATEST(entities.last_seen, NEW.timestamp),
            updated_at = CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_upsert_entity_on_anomaly
    AFTER INSERT ON anomalies FOR EACH ROW
    EXECUTE FUNCTION upsert_entity_on_anomaly();

-- Backfill entities from existing anomalies (safe to re-run)
INSERT INTO entities (entity_id, entity_type, risk_score, anomaly_count, first_seen, last_seen)
SELECT entity_id, COALESCE(entity_type, 'user'), MAX(COALESCE(risk_score, 0)), COUNT(*), MIN(timestamp), MAX(timestamp)
FROM anomalies WHERE entity_id IS NOT NULL
GROUP BY entity_id, COALESCE(entity_type, 'user')
ON CONFLICT (entity_id, entity_type) DO NOTHING;

-- Triggers for updated_at
CREATE TRIGGER update_models_updated_at BEFORE UPDATE ON models
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cases_updated_at BEFORE UPDATE ON cases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rules_updated_at BEFORE UPDATE ON rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_model_versions_updated_at BEFORE UPDATE ON model_versions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_entities_updated_at BEFORE UPDATE ON entities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Source Groups table: configuration for data ingestion sources
CREATE TABLE source_groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    config JSONB, -- Stores list of source definitions
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_source_groups_slug ON source_groups(slug);

CREATE TRIGGER update_source_groups_updated_at BEFORE UPDATE ON source_groups
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Integration settings table: configurable external service connections
CREATE TABLE IF NOT EXISTS integration_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    integration_type TEXT UNIQUE NOT NULL, -- 'ollama', 'openai', 'claude', 'gemini', 'elasticsearch', 'spark'
    enabled BOOLEAN DEFAULT false,
    config JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_integration_settings_type ON integration_settings(integration_type);

CREATE TRIGGER update_integration_settings_updated_at BEFORE UPDATE ON integration_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Extend users table with additional columns
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name VARCHAR(255);

-- Role permissions table: configurable per-role page access
CREATE TABLE IF NOT EXISTS role_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role VARCHAR(50) NOT NULL,
    page VARCHAR(50) NOT NULL,
    can_read BOOLEAN DEFAULT false,
    can_write BOOLEAN DEFAULT false,
    UNIQUE(role, page)
);

CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON role_permissions(role);

-- Notifications table: persistent user notifications
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    type VARCHAR(50) DEFAULT 'info',
    read BOOLEAN DEFAULT false,
    link VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);

-- Add circular FK constraint
ALTER TABLE models
ADD CONSTRAINT fk_models_default_version
FOREIGN KEY (default_version_id)
REFERENCES model_versions(id)
ON DELETE SET NULL;
