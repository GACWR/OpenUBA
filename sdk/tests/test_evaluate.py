'''
Copyright 2019-Present The OpenUBA Platform Authors
tests for the SDK detection-evaluation surface (issue #35)
'''

from unittest.mock import patch, MagicMock

from openuba.client import OpenUBAClient


class TestEvaluateSDK:
    def setup_method(self):
        self.client = OpenUBAClient(api_url="http://test:8000", token="test-token")

    @patch('openuba.client.requests.post')
    def test_evaluate_run_builds_payload_and_hits_endpoint(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"precision": 1.0, "recall": 0.5, "f1": 0.666667},
        )
        mock_post.return_value.raise_for_status = MagicMock()

        result = self.client.evaluate_run(
            "run-123", ["bad1", "bad2"],
            all_entities=["bad1", "bad2", "g1"],
            threshold=60,
            scenarios={"exfil": ["bad1"]},
        )

        assert result["recall"] == 0.5
        args, kwargs = mock_post.call_args
        assert args[0].endswith("/api/v1/evaluate/run")
        body = kwargs["json"]
        assert body["run_id"] == "run-123"
        assert body["malicious_entities"] == ["bad1", "bad2"]
        assert body["threshold"] == 60
        assert body["all_entities"] == ["bad1", "bad2", "g1"]
        assert body["scenarios"] == {"exfil": ["bad1"]}

    @patch('openuba.client.requests.post')
    def test_evaluate_run_minimal_payload(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"recall": 0.0})
        mock_post.return_value.raise_for_status = MagicMock()
        self.client.evaluate_run("run-9", ["bad1"])
        body = mock_post.call_args.kwargs["json"]
        assert body == {"run_id": "run-9", "malicious_entities": ["bad1"], "threshold": 50.0}

    @patch('openuba.client.requests.get')
    def test_query_anomalies_scopes_by_run(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {"items": []})
        mock_get.return_value.raise_for_status = MagicMock()
        self.client.query_anomalies(run_id="run-42")
        params = mock_get.call_args.kwargs["params"]
        assert params["run_id"] == "run-42"
