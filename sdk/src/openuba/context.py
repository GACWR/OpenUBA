'''
Copyright 2019-Present The OpenUBA Platform Authors
model context for train/infer execution in runner pods
'''

import os
import logging
import requests
import time
from threading import Thread
from queue import Queue

logger = logging.getLogger(__name__)


class ModelContext:
    '''
    execution context provided to models during train/infer
    handles metric reporting, logging, artifact management
    '''

    def __init__(self, job_id=None, model_id=None, run_type="train"):
        self.job_id = job_id or os.environ.get("JOB_ID")
        self.model_id = model_id or os.environ.get("MODEL_ID")
        self.run_type = run_type
        self.api_url = os.environ.get("OPENUBA_API_URL", "http://localhost:8000")
        self._metric_queue = Queue()
        self._log_queue = Queue()
        self._flush_interval = int(os.environ.get("METRICS_FLUSH_INTERVAL", "2"))
        self._running = False

    def start(self):
        '''start background metric/log flushing'''
        self._running = True
        self._flush_thread = Thread(target=self._flush_loop, daemon=True)
        self._flush_thread.start()

    def stop(self):
        '''stop background flushing and flush remaining'''
        self._running = False
        self._flush_metrics()
        self._flush_logs()

    def log_metric(self, name, value, epoch=None, step=None):
        '''log a training metric'''
        self._metric_queue.put({
            "metric_name": name,
            "metric_value": float(value),
            "epoch": epoch,
            "step": step,
        })

    def log(self, message, level="info"):
        '''log a message'''
        self._log_queue.put({
            "message": str(message),
            "level": level,
        })

    def set_progress(self, progress):
        '''update job progress (0-100)'''
        if self.job_id:
            try:
                requests.patch(
                    f"{self.api_url}/api/v1/jobs/{self.job_id}",
                    json={"progress": int(progress)},
                    timeout=5,
                )
            except Exception as e:
                logger.warning(f"failed to update progress: {e}")

    def _flush_loop(self):
        '''background loop to flush metrics and logs'''
        while self._running:
            self._flush_metrics()
            self._flush_logs()
            time.sleep(self._flush_interval)

    def _flush_metrics(self):
        '''send buffered metrics to API'''
        while not self._metric_queue.empty():
            metric = self._metric_queue.get()
            if self.job_id:
                try:
                    requests.post(
                        f"{self.api_url}/api/v1/internal/metrics/{self.job_id}",
                        json=metric,
                        timeout=5,
                    )
                except Exception as e:
                    logger.warning(f"failed to post metric: {e}")

    def _flush_logs(self):
        '''send buffered logs to API'''
        while not self._log_queue.empty():
            log_entry = self._log_queue.get()
            if self.job_id:
                try:
                    requests.post(
                        f"{self.api_url}/api/v1/internal/logs/{self.job_id}",
                        json=log_entry,
                        timeout=5,
                    )
                except Exception as e:
                    logger.warning(f"failed to post log: {e}")
