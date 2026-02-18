-- PostgreSQL triggers for real-time updates via NOTIFY
-- These enable PostGraphile subscriptions

-- Function to notify on anomaly changes
CREATE OR REPLACE FUNCTION notify_anomaly_change()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'anomaly_changed',
        json_build_object(
            'operation', TG_OP,
            'id', NEW.id,
            'entity_id', NEW.entity_id,
            'risk_score', NEW.risk_score
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for anomaly inserts/updates
DROP TRIGGER IF EXISTS anomaly_notify ON anomalies;
CREATE TRIGGER anomaly_notify
    AFTER INSERT OR UPDATE ON anomalies
    FOR EACH ROW
    EXECUTE FUNCTION notify_anomaly_change();

-- Function to notify on case changes
CREATE OR REPLACE FUNCTION notify_case_change()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'case_changed',
        json_build_object(
            'operation', TG_OP,
            'id', NEW.id,
            'title', NEW.title,
            'status', NEW.status
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for case inserts/updates
DROP TRIGGER IF EXISTS case_notify ON cases;
CREATE TRIGGER case_notify
    AFTER INSERT OR UPDATE ON cases
    FOR EACH ROW
    EXECUTE FUNCTION notify_case_change();

-- Function to notify on model execution
CREATE OR REPLACE FUNCTION notify_execution_change()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'execution_changed',
        json_build_object(
            'operation', TG_OP,
            'id', NEW.id,
            'model_id', NEW.model_id,
            'status', NEW.status
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for execution log changes
DROP TRIGGER IF EXISTS execution_notify ON execution_logs;
CREATE TRIGGER execution_notify
    AFTER INSERT OR UPDATE ON execution_logs
    FOR EACH ROW
    EXECUTE FUNCTION notify_execution_change();

