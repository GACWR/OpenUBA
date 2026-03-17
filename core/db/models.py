'''
Copyright 2019-Present The OpenUBA Platform Authors
sqlalchemy models for openuba database
'''

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DECIMAL, TIMESTAMP, ForeignKey, JSON
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
    default_version_id = Column(UUID(as_uuid=True), ForeignKey("model_versions.id", ondelete="SET NULL", name="fk_models_default_version_id", use_alter=True))
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


# ─── Workspace System (Phase 1) ───────────────────────────────────────────────


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    environment = Column(String(100), default="default")
    hardware_tier = Column(String(50), default="cpu-small")
    ide = Column(String(50), default="jupyterlab")
    status = Column(String(50), default="pending")
    pod_name = Column(String(255))
    service_name = Column(String(255))
    pvc_name = Column(String(255))
    access_url = Column(Text)
    node_port = Column(Integer)
    cr_name = Column(String(255))
    error_message = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    started_at = Column(TIMESTAMP(timezone=True))
    stopped_at = Column(TIMESTAMP(timezone=True))
    timeout_hours = Column(Integer, default=24)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # relationships
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<Workspace(id={self.id}, name={self.name}, status={self.status})>"


class Environment(Base):
    __tablename__ = "environments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    display_name = Column(String(255))
    description = Column(Text)
    docker_image = Column(Text, nullable=False)
    default_packages = Column(JSONB)
    hardware_requirements = Column(JSONB)
    enabled = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<Environment(name={self.name}, enabled={self.enabled})>"


# ─── Dataset Management (Phase 2) ─────────────────────────────────────────────


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    source_type = Column(String(50), default="upload")
    file_path = Column(Text)
    file_size = Column(Integer)
    row_count = Column(Integer)
    column_count = Column(Integer)
    columns = Column(JSONB)
    format = Column(String(50), default="csv")
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # relationships
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<Dataset(id={self.id}, name={self.name}, format={self.format})>"


# ─── Jobs & Execution Engine (Phase 3) ────────────────────────────────────────


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255))
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="SET NULL"))
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="SET NULL"))
    model_run_id = Column(UUID(as_uuid=True))
    job_type = Column(String(50), nullable=False)
    status = Column(String(50), default="pending")
    cr_name = Column(String(255))
    k8s_job_name = Column(String(255))
    hardware_tier = Column(String(50), default="cpu-small")
    hyperparameters = Column(JSONB)
    metrics = Column(JSONB)
    progress = Column(Integer, default=0)
    epoch_current = Column(Integer)
    epoch_total = Column(Integer)
    loss = Column(Float)
    learning_rate = Column(Float)
    error_message = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    started_at = Column(TIMESTAMP(timezone=True))
    completed_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # relationships
    model = relationship("Model", foreign_keys=[model_id])
    dataset = relationship("Dataset", foreign_keys=[dataset_id])
    # model_run_id is a soft reference (no FK) so sync is done at read-time in the repository
    creator = relationship("User", foreign_keys=[created_by])
    job_logs = relationship("JobLog", back_populates="job", cascade="all, delete-orphan", order_by="JobLog.created_at")
    training_metrics = relationship("TrainingMetric", back_populates="job", cascade="all, delete-orphan", order_by="TrainingMetric.created_at")

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, job_type={self.job_type}, status={self.status})>"


class JobLog(Base):
    __tablename__ = "job_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    level = Column(String(20), default="info")
    message = Column(Text, nullable=False)
    logger_name = Column(String(255))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # relationships
    job = relationship("Job", back_populates="job_logs")

    def __repr__(self) -> str:
        return f"<JobLog(id={self.id}, level={self.level})>"


class TrainingMetric(Base):
    __tablename__ = "training_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    metric_name = Column(String(255), nullable=False)
    metric_value = Column(Float, nullable=False)
    epoch = Column(Integer)
    step = Column(Integer)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # relationships
    job = relationship("Job", back_populates="training_metrics")

    def __repr__(self) -> str:
        return f"<TrainingMetric(job_id={self.job_id}, name={self.metric_name}, value={self.metric_value})>"


# ─── Visualization Framework (Phase 4) ────────────────────────────────────────


class Visualization(Base):
    __tablename__ = "visualizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    backend = Column(String(50), nullable=False)
    output_type = Column(String(50), nullable=False)
    code = Column(Text)
    data = Column(JSONB)
    config = Column(JSONB)
    rendered_output = Column(Text)
    refresh_interval = Column(Integer, default=0)
    published = Column(Boolean, default=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # relationships
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<Visualization(id={self.id}, name={self.name}, backend={self.backend})>"


# ─── Dashboard Framework (Phase 5) ────────────────────────────────────────────


class Dashboard(Base):
    __tablename__ = "dashboards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    layout = Column(JSONB, default=[])
    published = Column(Boolean, default=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # relationships
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<Dashboard(id={self.id}, name={self.name}, published={self.published})>"


# ─── Feature Store & Experiment Tracking (Phase 6) ────────────────────────────


class FeatureGroup(Base):
    __tablename__ = "feature_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    entity = Column(String(100), default="default")
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # relationships
    features = relationship("Feature", back_populates="group", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<FeatureGroup(id={self.id}, name={self.name})>"


class Feature(Base):
    __tablename__ = "features"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey("feature_groups.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    dtype = Column(String(50))
    mean = Column(Float)
    std = Column(Float)
    min_val = Column(Float)
    max_val = Column(Float)
    null_rate = Column(Float)
    transform = Column(String(100))
    transform_params = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # relationships
    group = relationship("FeatureGroup", back_populates="features")

    def __repr__(self) -> str:
        return f"<Feature(id={self.id}, name={self.name}, dtype={self.dtype})>"


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # relationships
    runs = relationship("ExperimentRun", back_populates="experiment", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<Experiment(id={self.id}, name={self.name})>"


class ExperimentRun(Base):
    __tablename__ = "experiment_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"))
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="SET NULL"))
    parameters = Column(JSONB)
    metrics = Column(JSONB)
    status = Column(String(50), default="pending")
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # relationships
    experiment = relationship("Experiment", back_populates="runs")
    job = relationship("Job", foreign_keys=[job_id])
    model = relationship("Model", foreign_keys=[model_id])
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<ExperimentRun(id={self.id}, experiment_id={self.experiment_id}, status={self.status})>"


class HyperparameterSet(Base):
    __tablename__ = "hyperparameter_sets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="SET NULL"))
    parameters = Column(JSONB, nullable=False)
    description = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # relationships
    model = relationship("Model", foreign_keys=[model_id])
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<HyperparameterSet(id={self.id}, name={self.name})>"


# ─── Pipeline System (Phase 7) ────────────────────────────────────────────────


class Pipeline(Base):
    __tablename__ = "pipelines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    steps = Column(JSONB, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # relationships
    pipeline_runs = relationship("PipelineRun", back_populates="pipeline", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<Pipeline(id={self.id}, name={self.name})>"


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="pending")
    current_step = Column(Integer, default=0)
    step_statuses = Column(JSONB, default=[])
    started_at = Column(TIMESTAMP(timezone=True))
    completed_at = Column(TIMESTAMP(timezone=True))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # relationships
    pipeline = relationship("Pipeline", back_populates="pipeline_runs")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<PipelineRun(id={self.id}, pipeline_id={self.pipeline_id}, status={self.status})>"

