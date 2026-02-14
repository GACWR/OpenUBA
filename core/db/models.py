'''
Copyright 2019-Present The OpenUBA Platform Authors
sqlalchemy models for openuba database
'''

from sqlalchemy import Column, String, Integer, Boolean, Text, DECIMAL, TIMESTAMP, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from core.db.connection import Base


class Model(Base):
    __tablename__ = "models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(Text, unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    display_name = Column(Text)
    version = Column(String(50), nullable=False)
    source_type = Column(String(50), nullable=False)
    source_url = Column(Text)
    manifest = Column(JSONB)
    status = Column(String(50), nullable=False, default="pending")
    enabled = Column(Boolean, default=True)
    description = Column(Text)
    author = Column(String(255))
    framework = Column(Text)
    runtime = Column(String(50), nullable=False, default="python-base")
    interface_version = Column(Integer, default=1)
    default_version_id = Column(UUID(as_uuid=True), ForeignKey("model_versions.id", ondelete="SET NULL"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # relationships
    versions = relationship("ModelVersion", back_populates="model", cascade="all, delete-orphan", foreign_keys="ModelVersion.model_id")
    components = relationship("ModelComponent", back_populates="model", cascade="all, delete-orphan")
    anomalies = relationship("Anomaly", back_populates="model", cascade="all, delete-orphan")
    execution_logs = relationship("ExecutionLog", back_populates="model", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Model(name={self.name}, version={self.version}, status={self.status})>"


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    version = Column(String(50), nullable=False)
    source_uri = Column(Text)
    code_backend = Column(Text)
    weights_backend = Column(Text)
    manifest = Column(JSONB)
    status = Column(Text, default="registered")
    code_path = Column(Text)
    requirements = Column(Text)
    encoding_hash = Column(Text)
    file_hash = Column(Text)
    installed_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # relationships
    model = relationship("Model", back_populates="versions", foreign_keys=[model_id])
    artifacts = relationship("ModelArtifact", back_populates="model_version", cascade="all, delete-orphan")
    runs = relationship("ModelRun", back_populates="model_version", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ModelVersion(model_id={self.model_id}, version={self.version})>"


class ModelComponent(Base):
    __tablename__ = "model_components"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    component_type = Column(String(50), nullable=False)
    file_hash = Column(String(64), nullable=False)
    data_hash = Column(String(64))
    file_path = Column(Text)
    file_size = Column(Integer)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # relationships
    model = relationship("Model", back_populates="components")

    def __repr__(self) -> str:
        return f"<ModelComponent(model_id={self.model_id}, filename={self.filename})>"


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"))
    run_id = Column(UUID(as_uuid=True), ForeignKey("model_runs.id", ondelete="SET NULL"))
    entity_id = Column(String(255))
    entity_type = Column(String(50), default="user")
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    risk_score = Column(DECIMAL(10, 2))
    anomaly_type = Column(String(100))
    details = Column(JSONB)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(TIMESTAMP(timezone=True))
    acknowledged_by = Column(String(255))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # relationships
    model = relationship("Model", back_populates="anomalies")
    case_links = relationship("CaseAnomaly", back_populates="anomaly")
    feedback = relationship("UserFeedback", back_populates="anomaly", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Anomaly(id={self.id}, entity_id={self.entity_id}, risk_score={self.risk_score})>"


class Entity(Base):
    __tablename__ = "entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(String(255), nullable=False)
    entity_type = Column(String(50), nullable=False, default="user")
    display_name = Column(String(255))
    risk_score = Column(DECIMAL(10, 2), default=0)
    anomaly_count = Column(Integer, default=0)
    first_seen = Column(TIMESTAMP(timezone=True))
    last_seen = Column(TIMESTAMP(timezone=True))
    entity_metadata = Column("metadata", JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<Entity(entity_id={self.entity_id}, entity_type={self.entity_type}, risk_score={self.risk_score})>"


class Case(Base):
    __tablename__ = "cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), nullable=False, default="open")
    severity = Column(String(20), default="medium")
    analyst_notes = Column(Text)
    assigned_to = Column(String(255))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    resolved_at = Column(TIMESTAMP(timezone=True))

    # relationships
    anomaly_links = relationship("CaseAnomaly", back_populates="case", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Case(id={self.id}, title={self.title}, status={self.status})>"


class CaseAnomaly(Base):
    __tablename__ = "case_anomalies"

    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), primary_key=True)
    anomaly_id = Column(UUID(as_uuid=True), ForeignKey("anomalies.id", ondelete="CASCADE"), primary_key=True)

    # relationships
    case = relationship("Case", back_populates="anomaly_links")
    anomaly = relationship("Anomaly", back_populates="case_links")


class Rule(Base):
    __tablename__ = "rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    rule_type = Column(String(50), nullable=False)
    condition = Column(Text, nullable=False)
    features = Column(Text)
    score = Column(Integer, default=0)
    enabled = Column(Boolean, default=True)
    severity = Column(String(20), default="medium")
    flow_graph = Column(JSONB)
    last_triggered_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # relationships
    alerts = relationship("Alert", back_populates="rule", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Rule(id={self.id}, name={self.name}, enabled={self.enabled})>"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("rules.id", ondelete="CASCADE"), nullable=False)
    severity = Column(String(20), nullable=False, default="medium")
    message = Column(Text, nullable=False)
    entity_id = Column(String(255))
    entity_type = Column(String(50), default="user")
    alert_context = Column("context", JSONB)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(TIMESTAMP(timezone=True))
    acknowledged_by = Column(String(255))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # relationships
    rule = relationship("Rule", back_populates="alerts")

    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, rule_id={self.rule_id}, severity={self.severity})>"


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), nullable=False)
    started_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    completed_at = Column(TIMESTAMP(timezone=True))
    error_message = Column(Text)
    error_traceback = Column(Text)
    execution_time_seconds = Column(DECIMAL(10, 3))
    container_id = Column(String(255))
    resource_usage = Column(JSONB)
    output_summary = Column(JSONB)

    # relationships
    model = relationship("Model", back_populates="execution_logs")

    def __repr__(self) -> str:
        return f"<ExecutionLog(id={self.id}, model_id={self.model_id}, status={self.status})>"


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    anomaly_id = Column(UUID(as_uuid=True), ForeignKey("anomalies.id", ondelete="CASCADE"), nullable=False)
    feedback_type = Column(String(50), nullable=False)
    notes = Column(Text)
    user_id = Column(String(255))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # relationships
    anomaly = relationship("Anomaly", back_populates="feedback")

    def __repr__(self) -> str:
        return f"<UserFeedback(id={self.id}, anomaly_id={self.anomaly_id}, feedback_type={self.feedback_type})>"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255))
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="analyst")
    display_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    last_login_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # relationships
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role = Column(String(50), nullable=False)
    page = Column(String(50), nullable=False)
    can_read = Column(Boolean, default=False)
    can_write = Column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<RolePermission(role={self.role}, page={self.page}, r={self.can_read}, w={self.can_write})>"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    title = Column(String(255), nullable=False)
    message = Column(Text)
    type = Column(String(50), default="info")
    read = Column(Boolean, default=False)
    link = Column(String(255))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # relationships
    user = relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, title={self.title}, read={self.read})>"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_type = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(UUID(as_uuid=True))
    user_id = Column(String(255))
    details = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action_type={self.action_type}, created_at={self.created_at})>"


class ModelArtifact(Base):
    __tablename__ = "model_artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_version_id = Column(UUID(as_uuid=True), ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False)
    kind = Column(Text, nullable=False)  # 'checkpoint', 'encoder', 'baseline', etc.
    format = Column(Text, nullable=False)  # 'sklearn_pickle', 'torch_pt', 'tf_saved_model', 'joblib', 'custom'
    path = Column(Text, nullable=False)
    metrics = Column(JSONB)
    file_hash = Column(String(64), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # relationships
    model_version = relationship("ModelVersion", back_populates="artifacts")
    runs = relationship("ModelRun", back_populates="artifact")

    def __repr__(self) -> str:
        return f"<ModelArtifact(id={self.id}, model_version_id={self.model_version_id}, kind={self.kind})>"


class ModelRun(Base):
    __tablename__ = "model_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_version_id = Column(UUID(as_uuid=True), ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False)
    artifact_id = Column(UUID(as_uuid=True), ForeignKey("model_artifacts.id", ondelete="SET NULL"))
    run_type = Column(Text, nullable=False)  # 'train' | 'infer'
    status = Column(Text, nullable=False)  # 'pending', 'dispatched', 'running', 'succeeded', 'failed'
    data_loader_type = Column(Text)
    data_loader_context = Column(JSONB)
    params = Column(JSONB)
    result_summary = Column(JSONB)
    error_message = Column(Text)
    k8s_job_name = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    started_at = Column(TIMESTAMP(timezone=True))
    finished_at = Column(TIMESTAMP(timezone=True))

    # relationships
    model_version = relationship("ModelVersion", back_populates="runs")
    artifact = relationship("ModelArtifact", back_populates="runs")
    logs = relationship("ModelLog", back_populates="model_run", order_by="ModelLog.created_at")

    def __repr__(self) -> str:
        return f"<ModelRun(id={self.id}, model_version_id={self.model_version_id}, run_type={self.run_type}, status={self.status})>"


class ModelLog(Base):
    __tablename__ = "model_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_run_id = Column(UUID(as_uuid=True), ForeignKey("model_runs.id", ondelete="CASCADE"), nullable=False)
    level = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    logger_name = Column(String(255))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # relationships
    model_run = relationship("ModelRun", back_populates="logs")

    def __repr__(self) -> str:
        return f"<ModelLog(id={self.id}, level={self.level}, message={self.message[:50]})>"


class IntegrationSetting(Base):
    __tablename__ = "integration_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_type = Column(Text, unique=True, nullable=False)
    enabled = Column(Boolean, default=False)
    config = Column(JSONB, nullable=False, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<IntegrationSetting(type={self.integration_type}, enabled={self.enabled})>"


class SourceGroup(Base):
    __tablename__ = "source_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(Text, unique=True, nullable=False)
    description = Column(Text)
    config = Column(JSONB)  # Stores list of source definitions
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<SourceGroup(slug={self.slug})>"

