'''
Copyright 2019-Present The OpenUBA Platform Authors
tests for enhanced openuba sdk client
'''

import pytest
from unittest.mock import patch, MagicMock
from openuba.client import OpenUBAClient


class TestOpenUBAClient:
    '''test enhanced sdk client methods'''

    def setup_method(self):
        self.client = OpenUBAClient(
            api_url="http://test:8000",
            token="test-token",
        )

    # ─── Model Registration ─────────────────────────────────────────

    @patch('openuba.client.requests.post')
    def test_register_model(self, mock_post):
        '''test registering a model via SDK'''
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"model_id": "uuid-1", "name": "test-model", "version": "1.0.0"},
        )
        mock_post.return_value.raise_for_status = MagicMock()
        result = self.client.register_model("test-model", description="test")
        assert result["name"] == "test-model"
        mock_post.assert_called_once()

    @patch('openuba.client.requests.post')
    def test_register_model_with_framework(self, mock_post):
        '''test registering a model with explicit framework'''
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"model_id": "uuid-1", "name": "test-model", "version": "1.0.0"},
        )
        mock_post.return_value.raise_for_status = MagicMock()
        result = self.client.register_model("test-model", framework="pytorch")
        assert result["name"] == "test-model"
        call_args = mock_post.call_args
        assert "pytorch" in str(call_args)

    @patch('openuba.client.requests.post')
    def test_publish_version(self, mock_post):
        '''test publishing a model version'''
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"model_id": "uuid-1", "version_id": "v-1", "version": "2.0.0"},
        )
        mock_post.return_value.raise_for_status = MagicMock()
        result = self.client.publish_version("uuid-1", version="2.0.0", summary="improved")
        assert result["version"] == "2.0.0"
        mock_post.assert_called_once()

    @patch('openuba.client.requests.get')
    def test_load_model(self, mock_get):
        '''test loading a model by name'''
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"model_id": "uuid-1", "name": "test-model", "version": "1.0.0"},
        )
        mock_get.return_value.raise_for_status = MagicMock()
        result = self.client.load_model("test-model")
        assert result["name"] == "test-model"

    # ─── Jobs ───────────────────────────────────────────────────────

    @patch('openuba.client.requests.post')
    def test_start_training(self, mock_post):
        '''test starting a training job'''
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"id": "job-1", "status": "pending", "job_type": "training"},
        )
        mock_post.return_value.raise_for_status = MagicMock()
        result = self.client.start_training("model-1", hardware_tier="cpu-small")
        assert result["status"] == "pending"
        assert result["job_type"] == "training"

    @patch('openuba.client.requests.post')
    def test_start_inference(self, mock_post):
        '''test starting an inference job'''
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"id": "job-2", "status": "pending", "job_type": "inference"},
        )
        mock_post.return_value.raise_for_status = MagicMock()
        result = self.client.start_inference("model-1", hardware_tier="gpu-small")
        assert result["status"] == "pending"

    @patch('openuba.client.requests.get')
    def test_get_job(self, mock_get):
        '''test getting job details'''
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"id": "job-1", "status": "running", "progress": 50},
        )
        mock_get.return_value.raise_for_status = MagicMock()
        result = self.client.get_job("job-1")
        assert result["status"] == "running"
        assert result["progress"] == 50

    @patch('openuba.client.requests.get')
    def test_get_logs(self, mock_get):
        '''test getting job logs'''
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [{"message": "training started", "level": "info"}],
        )
        mock_get.return_value.raise_for_status = MagicMock()
        result = self.client.get_logs("job-1")
        assert len(result) == 1
        assert result[0]["message"] == "training started"

    @patch('openuba.client.requests.post')
    def test_post_log(self, mock_post):
        '''test posting a log entry'''
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {"id": "log-1", "message": "epoch 1 done", "level": "info"},
        )
        mock_post.return_value.raise_for_status = MagicMock()
        result = self.client.post_log("job-1", "epoch 1 done")
        assert result["message"] == "epoch 1 done"

    # ─── Datasets ───────────────────────────────────────────────────

    @patch('openuba.client.requests.get')
    def test_list_datasets(self, mock_get):
        '''test listing datasets'''
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [{"id": "ds-1", "name": "test-dataset"}],
        )
        mock_get.return_value.raise_for_status = MagicMock()
        result = self.client.list_datasets()
        assert len(result) == 1

    @patch('openuba.client.requests.get')
    def test_get_dataset(self, mock_get):
        '''test getting a dataset'''
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"id": "ds-1", "name": "test-dataset", "format": "csv"},
        )
        mock_get.return_value.raise_for_status = MagicMock()
        result = self.client.get_dataset("ds-1")
        assert result["name"] == "test-dataset"

    @patch('openuba.client.requests.post')
    def test_create_dataset(self, mock_post):
        '''test creating a dataset'''
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {"id": "ds-1", "name": "new-dataset", "format": "parquet"},
        )
        mock_post.return_value.raise_for_status = MagicMock()
        result = self.client.create_dataset("new-dataset", format="parquet")
        assert result["name"] == "new-dataset"
        assert result["format"] == "parquet"

    # ─── Visualizations ─────────────────────────────────────────────

    @patch('openuba.client.requests.get')
    def test_list_visualizations(self, mock_get):
        '''test listing visualizations'''
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [{"id": "viz-1", "name": "test-viz"}],
        )
        mock_get.return_value.raise_for_status = MagicMock()
        result = self.client.list_visualizations()
        assert len(result) == 1

    @patch('openuba.client.requests.post')
    def test_create_visualization(self, mock_post):
        '''test creating a visualization'''
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {"id": "viz-1", "name": "test-viz", "backend": "matplotlib"},
        )
        mock_post.return_value.raise_for_status = MagicMock()
        result = self.client.create_visualization("test-viz", backend="matplotlib")
        assert result["name"] == "test-viz"
        assert result["backend"] == "matplotlib"

    @patch('openuba.client.requests.post')
    def test_create_visualization_auto_output_type(self, mock_post):
        '''test that output_type is auto-detected from backend'''
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {"id": "viz-1", "name": "plotly-viz", "backend": "plotly"},
        )
        mock_post.return_value.raise_for_status = MagicMock()
        self.client.create_visualization("plotly-viz", backend="plotly")
        call_args = mock_post.call_args
        body = call_args[1]["json"] if "json" in call_args[1] else call_args[0][0]
        # the output_type should have been set automatically

    @patch('openuba.client.requests.post')
    def test_publish_visualization(self, mock_post):
        '''test publishing a visualization'''
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"id": "viz-1", "published": True},
        )
        mock_post.return_value.raise_for_status = MagicMock()
        result = self.client.publish_visualization("viz-1")
        assert result["published"] is True

    # ─── Dashboards ─────────────────────────────────────────────────

    @patch('openuba.client.requests.post')
    def test_create_dashboard(self, mock_post):
        '''test creating a dashboard'''
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"id": "dash-1", "name": "test-dash"},
        )
        mock_post.return_value.raise_for_status = MagicMock()
        result = self.client.create_dashboard("test-dash", layout=[])
        assert result["name"] == "test-dash"

    @patch('openuba.client.requests.put')
    def test_update_dashboard(self, mock_put):
        '''test updating a dashboard'''
        mock_put.return_value = MagicMock(
            status_code=200,
            json=lambda: {"id": "dash-1", "name": "updated-dash", "layout": [{"type": "chart"}]},
        )
        mock_put.return_value.raise_for_status = MagicMock()
        result = self.client.update_dashboard("dash-1", layout=[{"type": "chart"}])
        assert result["name"] == "updated-dash"

    @patch('openuba.client.requests.get')
    def test_list_dashboards(self, mock_get):
        '''test listing dashboards'''
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [{"id": "dash-1", "name": "test-dash"}],
        )
        mock_get.return_value.raise_for_status = MagicMock()
        result = self.client.list_dashboards()
        assert len(result) == 1

    # ─── Features ───────────────────────────────────────────────────

    @patch('openuba.client.requests.post')
    def test_create_features(self, mock_post):
        '''test creating a feature group with features'''
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # create_group call
                return MagicMock(
                    status_code=201,
                    json=lambda: {"id": "group-1", "name": "test-group"},
                    raise_for_status=MagicMock(),
                )
            else:
                # add_feature calls
                return MagicMock(
                    status_code=201,
                    json=lambda: {"id": f"feat-{call_count[0]}", "name": "feature"},
                    raise_for_status=MagicMock(),
                )
        mock_post.side_effect = side_effect
        result = self.client.create_features(
            ["feature_a", "feature_b"],
            "test-group",
            description="test group"
        )
        assert result["name"] == "test-group"
        assert mock_post.call_count == 3  # 1 group + 2 features

    @patch('openuba.client.requests.get')
    def test_load_features(self, mock_get):
        '''test loading feature group by name'''
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"id": "group-1", "name": "test-group", "features": []},
        )
        mock_get.return_value.raise_for_status = MagicMock()
        result = self.client.load_features("test-group")
        assert result["name"] == "test-group"

    # ─── Experiments ────────────────────────────────────────────────

    @patch('openuba.client.requests.post')
    def test_create_experiment(self, mock_post):
        '''test creating an experiment'''
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"id": "exp-1", "name": "test-exp"},
        )
        mock_post.return_value.raise_for_status = MagicMock()
        result = self.client.create_experiment("test-exp")
        assert result["name"] == "test-exp"

    @patch('openuba.client.requests.post')
    def test_add_experiment_run(self, mock_post):
        '''test adding a run to an experiment'''
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {"id": "run-1", "experiment_id": "exp-1", "status": "pending"},
        )
        mock_post.return_value.raise_for_status = MagicMock()
        result = self.client.add_experiment_run(
            "exp-1",
            parameters={"lr": 0.01},
            metrics={"acc": 0.9}
        )
        assert result["experiment_id"] == "exp-1"

    @patch('openuba.client.requests.get')
    def test_compare_experiment_runs(self, mock_get):
        '''test comparing experiment runs'''
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {"id": "run-1", "metrics": {"acc": 0.85}},
                {"id": "run-2", "metrics": {"acc": 0.92}},
            ],
        )
        mock_get.return_value.raise_for_status = MagicMock()
        result = self.client.compare_experiment_runs("exp-1")
        assert len(result) == 2

    # ─── Hyperparameters ────────────────────────────────────────────

    @patch('openuba.client.requests.post')
    def test_create_hyperparameters(self, mock_post):
        '''test creating a hyperparameter set'''
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {"id": "hp-1", "name": "hp-set", "parameters": {"lr": 0.01}},
        )
        mock_post.return_value.raise_for_status = MagicMock()
        result = self.client.create_hyperparameters("hp-set", {"lr": 0.01})
        assert result["name"] == "hp-set"

    @patch('openuba.client.requests.get')
    def test_load_hyperparameters(self, mock_get):
        '''test loading hyperparameter set'''
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"id": "hp-1", "name": "hp-set", "parameters": {"lr": 0.01}},
        )
        mock_get.return_value.raise_for_status = MagicMock()
        result = self.client.load_hyperparameters("hp-set")
        assert result["parameters"]["lr"] == 0.01

    # ─── Pipelines ──────────────────────────────────────────────────

    @patch('openuba.client.requests.post')
    def test_create_pipeline(self, mock_post):
        '''test creating a pipeline'''
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {"id": "pipe-1", "name": "test-pipe", "steps": [{"name": "step1"}]},
        )
        mock_post.return_value.raise_for_status = MagicMock()
        result = self.client.create_pipeline("test-pipe", [{"name": "step1"}])
        assert result["name"] == "test-pipe"

    @patch('openuba.client.requests.post')
    def test_run_pipeline(self, mock_post):
        '''test running a pipeline'''
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {"id": "run-1", "pipeline_id": "pipe-1", "status": "pending"},
        )
        mock_post.return_value.raise_for_status = MagicMock()
        result = self.client.run_pipeline("pipe-1")
        assert result["status"] == "pending"

    # ─── UBA Queries ────────────────────────────────────────────────

    @patch('openuba.client.requests.get')
    def test_query_anomalies(self, mock_get):
        '''test querying anomalies'''
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [{"id": "a-1", "risk_score": 0.9}],
        )
        mock_get.return_value.raise_for_status = MagicMock()
        result = self.client.query_anomalies(min_risk=0.7)
        assert len(result) == 1
        assert result[0]["risk_score"] == 0.9

    @patch('openuba.client.requests.get')
    def test_query_anomalies_with_filters(self, mock_get):
        '''test querying anomalies with multiple filters'''
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [],
        )
        mock_get.return_value.raise_for_status = MagicMock()
        result = self.client.query_anomalies(
            entity_id="user-123",
            min_risk=0.5,
            max_risk=0.9,
            limit=50
        )
        assert isinstance(result, list)

    @patch('openuba.client.requests.get')
    def test_get_entity_risk(self, mock_get):
        '''test getting entity risk profile'''
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"entity_id": "user-123", "risk_score": 0.75},
        )
        mock_get.return_value.raise_for_status = MagicMock()
        result = self.client.get_entity_risk("user-123")
        assert result["entity_id"] == "user-123"

    @patch('openuba.client.requests.get')
    def test_query_cases(self, mock_get):
        '''test querying cases'''
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [{"id": "case-1", "status": "open", "severity": "high"}],
        )
        mock_get.return_value.raise_for_status = MagicMock()
        result = self.client.query_cases(status="open", severity="high")
        assert len(result) == 1

    @patch('openuba.client.requests.get')
    def test_list_rules(self, mock_get):
        '''test listing rules'''
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [{"id": "rule-1", "name": "test-rule", "enabled": True}],
        )
        mock_get.return_value.raise_for_status = MagicMock()
        result = self.client.list_rules(enabled=True)
        assert len(result) == 1

    # ─── Framework Detection ────────────────────────────────────────

    def test_detect_framework_sklearn(self):
        '''test detecting sklearn framework'''
        model = MagicMock()
        model.__class__.__module__ = 'sklearn.ensemble._forest'
        result = OpenUBAClient._detect_framework(model)
        assert result == 'sklearn'

    def test_detect_framework_pytorch(self):
        '''test detecting pytorch framework'''
        model = MagicMock()
        model.__class__.__module__ = 'torch.nn.modules.container'
        result = OpenUBAClient._detect_framework(model)
        assert result == 'pytorch'

    def test_detect_framework_tensorflow(self):
        '''test detecting tensorflow framework'''
        model = MagicMock()
        model.__class__.__module__ = 'tensorflow.python.keras.engine'
        result = OpenUBAClient._detect_framework(model)
        assert result == 'tensorflow'

    def test_detect_framework_keras(self):
        '''test detecting keras framework (tensorflow backend)'''
        model = MagicMock()
        model.__class__.__module__ = 'keras.src.models'
        result = OpenUBAClient._detect_framework(model)
        assert result == 'tensorflow'

    def test_detect_framework_networkx(self):
        '''test detecting networkx framework'''
        model = MagicMock()
        model.__class__.__module__ = 'networkx.classes.graph'
        result = OpenUBAClient._detect_framework(model)
        assert result == 'networkx'

    def test_detect_framework_unknown(self):
        '''test detecting unknown framework'''
        model = MagicMock()
        model.__class__.__module__ = 'custom.module'
        result = OpenUBAClient._detect_framework(model)
        assert result == 'unknown'

    # ─── Client Initialization ──────────────────────────────────────

    def test_client_init_defaults(self):
        '''test client initialization with defaults'''
        client = OpenUBAClient()
        assert client.api_url == "http://localhost:8000"
        assert client.token is None

    def test_client_init_custom(self):
        '''test client initialization with custom values'''
        client = OpenUBAClient(
            api_url="http://custom:9000",
            token="my-token",
        )
        assert client.api_url == "http://custom:9000"
        assert client.token == "my-token"

    def test_client_workspace_id(self):
        '''test that workspace_id is read from environment'''
        import os
        os.environ["OPENUBA_WORKSPACE_ID"] = "ws-test-123"
        try:
            client = OpenUBAClient()
            assert client.workspace_id == "ws-test-123"
        finally:
            del os.environ["OPENUBA_WORKSPACE_ID"]

    def test_client_headers(self):
        '''test that auth headers are set correctly'''
        headers = self.client._headers()
        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer test-token"

    def test_client_headers_no_token(self):
        '''test headers without token'''
        client = OpenUBAClient(api_url="http://test:8000")
        headers = client._headers()
        assert headers["Content-Type"] == "application/json"
        assert "Authorization" not in headers
