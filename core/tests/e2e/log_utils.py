'''
Copyright 2019-Present The OpenUBA Platform Authors
log verification utilities for e2e testing
'''

import logging
from typing import Dict, List, Optional
from core.tests.e2e.k8s_utils import K8sTestUtils

logger = logging.getLogger(__name__)


class LogTestUtils:
    '''
    utilities for verifying container logs in e2e tests
    '''

    def __init__(self, k8s_utils: K8sTestUtils):
        self.k8s_utils = k8s_utils

    def get_backend_logs(self, tail_lines: int = 100) -> Dict[str, str]:
        '''
        get logs from backend pods
        '''
        return self.k8s_utils.get_pod_logs(
            label_selector="app=backend",
            tail_lines=tail_lines
        )

    def get_frontend_logs(self, tail_lines: int = 100) -> Dict[str, str]:
        '''
        get logs from frontend pods
        '''
        return self.k8s_utils.get_pod_logs(
            label_selector="app=frontend",
            tail_lines=tail_lines
        )

    def check_logs_for_errors(
        self,
        logs: Dict[str, str],
        exclude_keywords: Optional[List[str]] = None
    ) -> List[str]:
        '''
        check logs for error messages
        returns list of error lines found
        '''
        if exclude_keywords is None:
            exclude_keywords = ["deprecation", "warning"]

        errors = []
        for pod_name, log_content in logs.items():
            lines = log_content.split("\n")
            for line in lines:
                line_lower = line.lower()
                # check for error indicators
                if any(keyword in line_lower for keyword in ["error", "exception", "traceback", "failed"]):
                    # exclude known non-critical errors
                    if not any(exclude in line_lower for exclude in exclude_keywords):
                        errors.append(f"{pod_name}: {line}")

        return errors

    def verify_expected_log_message(
        self,
        logs: Dict[str, str],
        expected_message: str
    ) -> bool:
        '''
        verify expected message appears in logs
        '''
        for log_content in logs.values():
            if expected_message in log_content:
                return True
        return False

    def get_recent_backend_errors(self, tail_lines: int = 200) -> List[str]:
        '''
        get recent errors from backend logs
        '''
        logs = self.get_backend_logs(tail_lines=tail_lines)
        return self.check_logs_for_errors(logs)

    def get_recent_frontend_errors(self, tail_lines: int = 200) -> List[str]:
        '''
        get recent errors from frontend logs
        '''
        logs = self.get_frontend_logs(tail_lines=tail_lines)
        return self.check_logs_for_errors(logs)

