'''
Copyright 2019-Present The OpenUBA Platform Authors
tests for model context module
'''

import pytest
from unittest.mock import patch, MagicMock, call
from openuba.context import ModelContext


class TestModelContext:
    '''test ModelContext execution context methods'''

    def setup_method(self):
        self.ctx = ModelContext(
            job_id="test-job-123",
            model_id="test-model-456",
            run_type="train",
        )

    # ─── Initialization ─────────────────────────────────────────────

    def test_init_with_params(self):
        '''test initialization with explicit parameters'''
        ctx = ModelContext(job_id="j-1", model_id="m-1", run_type="infer")
        assert ctx.job_id == "j-1"
        assert ctx.model_id == "m-1"
        assert ctx.run_type == "infer"

    def test_init_defaults(self):
        '''test initialization with defaults'''
        ctx = ModelContext()
        assert ctx.run_type == "train"
        assert ctx.api_url == "http://localhost:8000"

    def test_init_from_environment(self):
        '''test initialization reads from environment variables'''
        import os
        os.environ["JOB_ID"] = "env-job-id"
        os.environ["MODEL_ID"] = "env-model-id"
        os.environ["OPENUBA_API_URL"] = "http://custom:9000"
        try:
            ctx = ModelContext()
            assert ctx.job_id == "env-job-id"
            assert ctx.model_id == "env-model-id"
            assert ctx.api_url == "http://custom:9000"
        finally:
            del os.environ["JOB_ID"]
            del os.environ["MODEL_ID"]
            del os.environ["OPENUBA_API_URL"]

    # ─── Metric Logging ─────────────────────────────────────────────

    def test_log_metric(self):
        '''test logging a metric adds to queue'''
        self.ctx.log_metric("loss", 0.5, epoch=1, step=100)
        assert not self.ctx._metric_queue.empty()
        metric = self.ctx._metric_queue.get()
        assert metric["metric_name"] == "loss"
        assert metric["metric_value"] == 0.5
        assert metric["epoch"] == 1
        assert metric["step"] == 100

    def test_log_metric_value_conversion(self):
        '''test that metric values are converted to float'''
        self.ctx.log_metric("accuracy", 92, epoch=1)
        metric = self.ctx._metric_queue.get()
        assert isinstance(metric["metric_value"], float)
        assert metric["metric_value"] == 92.0

    def test_log_metric_optional_fields(self):
        '''test logging a metric without optional fields'''
        self.ctx.log_metric("test_metric", 1.0)
        metric = self.ctx._metric_queue.get()
        assert metric["epoch"] is None
        assert metric["step"] is None

    # ─── Log Messages ───────────────────────────────────────────────

    def test_log_message(self):
        '''test logging a message adds to queue'''
        self.ctx.log("training started", level="info")
        assert not self.ctx._log_queue.empty()
        log_entry = self.ctx._log_queue.get()
        assert log_entry["message"] == "training started"
        assert log_entry["level"] == "info"

    def test_log_message_default_level(self):
        '''test logging a message with default level'''
        self.ctx.log("some message")
        log_entry = self.ctx._log_queue.get()
        assert log_entry["level"] == "info"

    def test_log_message_error_level(self):
        '''test logging an error message'''
        self.ctx.log("something went wrong", level="error")
        log_entry = self.ctx._log_queue.get()
        assert log_entry["level"] == "error"

    def test_log_message_converts_to_string(self):
        '''test that log message is converted to string'''
        self.ctx.log(12345)
        log_entry = self.ctx._log_queue.get()
        assert log_entry["message"] == "12345"

    # ─── Progress Updates ───────────────────────────────────────────

    @patch('openuba.context.requests.patch')
    def test_set_progress(self, mock_patch):
        '''test setting job progress'''
        self.ctx.set_progress(50)
        mock_patch.assert_called_once_with(
            "http://localhost:8000/api/v1/jobs/test-job-123",
            json={"progress": 50},
        )

    @patch('openuba.context.requests.patch')
    def test_set_progress_no_job_id(self, mock_patch):
        '''test that set_progress does nothing without job_id'''
        ctx = ModelContext(job_id=None)
        ctx.set_progress(50)
        mock_patch.assert_not_called()

    @patch('openuba.context.requests.patch')
    def test_set_progress_handles_error(self, mock_patch):
        '''test that set_progress handles request errors gracefully'''
        mock_patch.side_effect = Exception("connection error")
        # should not raise
        self.ctx.set_progress(75)

    # ─── Metric Flushing ────────────────────────────────────────────

    @patch('openuba.context.requests.post')
    def test_flush_metrics(self, mock_post):
        '''test flushing metrics sends them to API'''
        self.ctx.log_metric("loss", 0.5, epoch=1)
        self.ctx.log_metric("accuracy", 0.85, epoch=1)
        self.ctx._flush_metrics()
        assert mock_post.call_count == 2
        assert self.ctx._metric_queue.empty()

    @patch('openuba.context.requests.post')
    def test_flush_metrics_no_job_id(self, mock_post):
        '''test flushing metrics without job_id does not call API'''
        ctx = ModelContext(job_id=None)
        ctx.log_metric("loss", 0.5)
        ctx._flush_metrics()
        mock_post.assert_not_called()

    @patch('openuba.context.requests.post')
    def test_flush_metrics_handles_error(self, mock_post):
        '''test that flush_metrics handles request errors gracefully'''
        mock_post.side_effect = Exception("connection error")
        self.ctx.log_metric("loss", 0.5)
        # should not raise
        self.ctx._flush_metrics()

    # ─── Log Flushing ───────────────────────────────────────────────

    @patch('openuba.context.requests.post')
    def test_flush_logs(self, mock_post):
        '''test flushing logs sends them to API'''
        self.ctx.log("message 1")
        self.ctx.log("message 2")
        self.ctx._flush_logs()
        assert mock_post.call_count == 2
        assert self.ctx._log_queue.empty()

    @patch('openuba.context.requests.post')
    def test_flush_logs_no_job_id(self, mock_post):
        '''test flushing logs without job_id does not call API'''
        ctx = ModelContext(job_id=None)
        ctx.log("test message")
        ctx._flush_logs()
        mock_post.assert_not_called()

    @patch('openuba.context.requests.post')
    def test_flush_logs_handles_error(self, mock_post):
        '''test that flush_logs handles request errors gracefully'''
        mock_post.side_effect = Exception("connection error")
        self.ctx.log("test message")
        # should not raise
        self.ctx._flush_logs()

    # ─── Start/Stop Lifecycle ───────────────────────────────────────

    @patch('openuba.context.requests.post')
    def test_start_and_stop(self, mock_post):
        '''test start begins background flushing and stop flushes remaining'''
        self.ctx.log_metric("loss", 0.5)
        self.ctx.log("started")
        self.ctx.start()
        assert self.ctx._running is True
        self.ctx.stop()
        assert self.ctx._running is False
        # after stop, all queues should be flushed
        assert self.ctx._metric_queue.empty()
        assert self.ctx._log_queue.empty()

    def test_stop_flushes_remaining(self):
        '''test that stop flushes remaining metrics and logs'''
        ctx = ModelContext(job_id=None)  # no job_id so no API calls
        ctx.log_metric("loss", 0.5)
        ctx.log("test")
        ctx.start()
        ctx.stop()
        # queues should be empty after stop
        assert ctx._metric_queue.empty()
        assert ctx._log_queue.empty()

    # ─── API URL Construction ───────────────────────────────────────

    @patch('openuba.context.requests.post')
    def test_flush_metrics_url(self, mock_post):
        '''test that metrics are posted to correct internal endpoint'''
        self.ctx.log_metric("loss", 0.5)
        self.ctx._flush_metrics()
        expected_url = "http://localhost:8000/api/v1/internal/metrics/test-job-123"
        mock_post.assert_called_once_with(
            expected_url,
            json={"metric_name": "loss", "metric_value": 0.5, "epoch": None, "step": None},
        )

    @patch('openuba.context.requests.post')
    def test_flush_logs_url(self, mock_post):
        '''test that logs are posted to correct internal endpoint'''
        self.ctx.log("test message", level="warning")
        self.ctx._flush_logs()
        expected_url = "http://localhost:8000/api/v1/internal/logs/test-job-123"
        mock_post.assert_called_once_with(
            expected_url,
            json={"message": "test message", "level": "warning"},
        )
