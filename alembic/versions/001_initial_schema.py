"""initial schema with all platform tables

Revision ID: 001
Revises: None
Create Date: 2026-03-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(255), unique=True, nullable=False),
        sa.Column('email', sa.String(255)),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), server_default='analyst'),
        sa.Column('display_name', sa.String(255)),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('last_login_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # models
    op.create_table(
        'models',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('slug', sa.Text, unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('display_name', sa.Text),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_url', sa.Text),
        sa.Column('manifest', postgresql.JSONB),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('enabled', sa.Boolean, server_default='true'),
        sa.Column('description', sa.Text),
        sa.Column('author', sa.String(255)),
        sa.Column('framework', sa.Text),
        sa.Column('runtime', sa.String(50), nullable=False, server_default='python-base'),
        sa.Column('interface_version', sa.Integer, server_default='1'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # model_versions
    op.create_table(
        'model_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('model_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('models.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('source_uri', sa.Text),
        sa.Column('code_backend', sa.Text),
        sa.Column('weights_backend', sa.Text),
        sa.Column('manifest', postgresql.JSONB),
        sa.Column('status', sa.Text, server_default='registered'),
        sa.Column('code_path', sa.Text),
        sa.Column('requirements', sa.Text),
        sa.Column('encoding_hash', sa.Text),
        sa.Column('file_hash', sa.Text),
        sa.Column('installed_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # add default_version_id FK to models (after model_versions exists)
    op.add_column('models', sa.Column('default_version_id', postgresql.UUID(as_uuid=True),
                                       sa.ForeignKey('model_versions.id', ondelete='SET NULL')))

    # workspaces
    op.create_table(
        'workspaces',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('environment', sa.String(100), server_default='default'),
        sa.Column('hardware_tier', sa.String(50), server_default='cpu-small'),
        sa.Column('ide', sa.String(50), server_default='jupyterlab'),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('pod_name', sa.String(255)),
        sa.Column('service_name', sa.String(255)),
        sa.Column('pvc_name', sa.String(255)),
        sa.Column('access_url', sa.Text),
        sa.Column('node_port', sa.Integer),
        sa.Column('cr_name', sa.String(255)),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('stopped_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('timeout_hours', sa.Integer, server_default='24'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # environments
    op.create_table(
        'environments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('display_name', sa.String(255)),
        sa.Column('description', sa.Text),
        sa.Column('docker_image', sa.Text, nullable=False),
        sa.Column('default_packages', postgresql.JSONB),
        sa.Column('hardware_requirements', postgresql.JSONB),
        sa.Column('enabled', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # datasets
    op.create_table(
        'datasets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('source_type', sa.String(50), server_default='upload'),
        sa.Column('file_path', sa.Text),
        sa.Column('file_size', sa.Integer),
        sa.Column('row_count', sa.Integer),
        sa.Column('column_count', sa.Integer),
        sa.Column('columns', postgresql.JSONB),
        sa.Column('format', sa.String(50), server_default='csv'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # jobs
    op.create_table(
        'jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255)),
        sa.Column('model_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('models.id', ondelete='SET NULL')),
        sa.Column('dataset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('datasets.id', ondelete='SET NULL')),
        sa.Column('job_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('cr_name', sa.String(255)),
        sa.Column('k8s_job_name', sa.String(255)),
        sa.Column('hardware_tier', sa.String(50), server_default='cpu-small'),
        sa.Column('hyperparameters', postgresql.JSONB),
        sa.Column('metrics', postgresql.JSONB),
        sa.Column('progress', sa.Integer, server_default='0'),
        sa.Column('epoch_current', sa.Integer),
        sa.Column('epoch_total', sa.Integer),
        sa.Column('loss', sa.Float),
        sa.Column('learning_rate', sa.Float),
        sa.Column('error_message', sa.Text),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=False),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # job_logs
    op.create_table(
        'job_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('level', sa.String(20), server_default='info'),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('logger_name', sa.String(255)),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # training_metrics
    op.create_table(
        'training_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('metric_name', sa.String(255), nullable=False),
        sa.Column('metric_value', sa.Float, nullable=False),
        sa.Column('epoch', sa.Integer),
        sa.Column('step', sa.Integer),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # visualizations
    op.create_table(
        'visualizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('backend', sa.String(50), nullable=False),
        sa.Column('output_type', sa.String(50), nullable=False),
        sa.Column('code', sa.Text),
        sa.Column('data', postgresql.JSONB),
        sa.Column('config', postgresql.JSONB),
        sa.Column('rendered_output', sa.Text),
        sa.Column('refresh_interval', sa.Integer, server_default='0'),
        sa.Column('published', sa.Boolean, server_default='false'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # dashboards
    op.create_table(
        'dashboards',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('layout', postgresql.JSONB),
        sa.Column('published', sa.Boolean, server_default='false'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # feature_groups
    op.create_table(
        'feature_groups',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text),
        sa.Column('entity', sa.String(100), server_default='default'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # features
    op.create_table(
        'features',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('feature_groups.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('dtype', sa.String(50)),
        sa.Column('mean', sa.Float),
        sa.Column('std', sa.Float),
        sa.Column('min_val', sa.Float),
        sa.Column('max_val', sa.Float),
        sa.Column('null_rate', sa.Float),
        sa.Column('transform', sa.String(100)),
        sa.Column('transform_params', postgresql.JSONB),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # experiments
    op.create_table(
        'experiments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # experiment_runs
    op.create_table(
        'experiment_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('experiment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('experiments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='SET NULL')),
        sa.Column('model_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('models.id', ondelete='SET NULL')),
        sa.Column('parameters', postgresql.JSONB),
        sa.Column('metrics', postgresql.JSONB),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # hyperparameter_sets
    op.create_table(
        'hyperparameter_sets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('model_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('models.id', ondelete='SET NULL')),
        sa.Column('parameters', postgresql.JSONB, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # pipelines
    op.create_table(
        'pipelines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('steps', postgresql.JSONB, nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # pipeline_runs
    op.create_table(
        'pipeline_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('pipeline_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('pipelines.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('current_step', sa.Integer, server_default='0'),
        sa.Column('step_statuses', postgresql.JSONB),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # remaining tables: anomalies, entities, cases, rules, alerts, etc.
    op.create_table(
        'model_components',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('model_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('models.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('component_type', sa.String(50), nullable=False),
        sa.Column('file_hash', sa.String(64), nullable=False),
        sa.Column('data_hash', sa.String(64)),
        sa.Column('file_path', sa.Text),
        sa.Column('file_size', sa.Integer),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'model_artifacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('model_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('model_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('kind', sa.Text, nullable=False),
        sa.Column('format', sa.Text, nullable=False),
        sa.Column('path', sa.Text, nullable=False),
        sa.Column('metrics', postgresql.JSONB),
        sa.Column('file_hash', sa.String(64), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'model_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('model_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('model_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('artifact_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('model_artifacts.id', ondelete='SET NULL')),
        sa.Column('run_type', sa.Text, nullable=False),
        sa.Column('status', sa.Text, nullable=False),
        sa.Column('data_loader_type', sa.Text),
        sa.Column('data_loader_context', postgresql.JSONB),
        sa.Column('params', postgresql.JSONB),
        sa.Column('result_summary', postgresql.JSONB),
        sa.Column('error_message', sa.Text),
        sa.Column('k8s_job_name', sa.Text),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('finished_at', sa.TIMESTAMP(timezone=True)),
    )

    op.create_table(
        'model_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('model_run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('model_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('level', sa.String(20), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('logger_name', sa.String(255)),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'entities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_id', sa.String(255), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False, server_default='user'),
        sa.Column('display_name', sa.String(255)),
        sa.Column('risk_score', sa.DECIMAL(10, 2), server_default='0'),
        sa.Column('anomaly_count', sa.Integer, server_default='0'),
        sa.Column('first_seen', sa.TIMESTAMP(timezone=True)),
        sa.Column('last_seen', sa.TIMESTAMP(timezone=True)),
        sa.Column('metadata', postgresql.JSONB),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'anomalies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('model_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('models.id', ondelete='CASCADE')),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('model_runs.id', ondelete='SET NULL')),
        sa.Column('entity_id', sa.String(255)),
        sa.Column('entity_type', sa.String(50), server_default='user'),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('risk_score', sa.DECIMAL(10, 2)),
        sa.Column('anomaly_type', sa.String(100)),
        sa.Column('details', postgresql.JSONB),
        sa.Column('acknowledged', sa.Boolean, server_default='false'),
        sa.Column('acknowledged_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('acknowledged_by', sa.String(255)),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'cases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('status', sa.String(50), nullable=False, server_default='open'),
        sa.Column('severity', sa.String(20), server_default='medium'),
        sa.Column('analyst_notes', sa.Text),
        sa.Column('assigned_to', sa.String(255)),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('resolved_at', sa.TIMESTAMP(timezone=True)),
    )

    op.create_table(
        'case_anomalies',
        sa.Column('case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cases.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('anomaly_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('anomalies.id', ondelete='CASCADE'), primary_key=True),
    )

    op.create_table(
        'rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('rule_type', sa.String(50), nullable=False),
        sa.Column('condition', sa.Text, nullable=False),
        sa.Column('features', sa.Text),
        sa.Column('score', sa.Integer, server_default='0'),
        sa.Column('enabled', sa.Boolean, server_default='true'),
        sa.Column('severity', sa.String(20), server_default='medium'),
        sa.Column('flow_graph', postgresql.JSONB),
        sa.Column('last_triggered_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('rule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('rules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('entity_id', sa.String(255)),
        sa.Column('entity_type', sa.String(50), server_default='user'),
        sa.Column('context', postgresql.JSONB),
        sa.Column('acknowledged', sa.Boolean, server_default='false'),
        sa.Column('acknowledged_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('acknowledged_by', sa.String(255)),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'execution_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('model_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('models.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('error_message', sa.Text),
        sa.Column('error_traceback', sa.Text),
        sa.Column('execution_time_seconds', sa.DECIMAL(10, 3)),
        sa.Column('container_id', sa.String(255)),
        sa.Column('resource_usage', postgresql.JSONB),
        sa.Column('output_summary', postgresql.JSONB),
    )

    op.create_table(
        'user_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('anomaly_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('anomalies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('feedback_type', sa.String(50), nullable=False),
        sa.Column('notes', sa.Text),
        sa.Column('user_id', sa.String(255)),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'role_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('page', sa.String(50), nullable=False),
        sa.Column('can_read', sa.Boolean, server_default='false'),
        sa.Column('can_write', sa.Boolean, server_default='false'),
    )

    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text),
        sa.Column('type', sa.String(50), server_default='info'),
        sa.Column('read', sa.Boolean, server_default='false'),
        sa.Column('link', sa.String(255)),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('action_type', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(50)),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True)),
        sa.Column('user_id', sa.String(255)),
        sa.Column('details', postgresql.JSONB),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'integration_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('integration_type', sa.Text, unique=True, nullable=False),
        sa.Column('enabled', sa.Boolean, server_default='false'),
        sa.Column('config', postgresql.JSONB, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'source_groups',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('slug', sa.Text, unique=True, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('config', postgresql.JSONB),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    tables = [
        'source_groups', 'integration_settings', 'audit_logs', 'notifications',
        'role_permissions', 'user_feedback', 'execution_logs', 'alerts', 'rules',
        'case_anomalies', 'cases', 'anomalies', 'entities', 'model_logs',
        'model_runs', 'model_artifacts', 'model_components', 'pipeline_runs',
        'pipelines', 'hyperparameter_sets', 'experiment_runs', 'experiments',
        'features', 'feature_groups', 'dashboards', 'visualizations',
        'training_metrics', 'job_logs', 'jobs', 'datasets', 'environments',
        'workspaces', 'model_versions', 'models', 'users',
    ]
    for table in tables:
        op.drop_table(table)
