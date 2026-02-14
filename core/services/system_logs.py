'''
Copyright 2019-Present The OpenUBA Platform Authors
System Log Service for fetching logs from K8s pods or local environment
'''

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

class SystemLogService:
    def __init__(self):
        self.k8s_available = False
        try:
            from kubernetes import client, config
            # Try to load in-cluster config first, then local kubeconfig
            try:
                config.load_incluster_config()
                self.k8s_available = True
                logger.info("Loaded in-cluster K8s config")
            except:
                try:
                    config.load_kube_config()
                    self.k8s_available = True
                    logger.info("Loaded local K8s config")
                except:
                    logger.warning("No K8s config found, falling back to local file logs")
        except ImportError:
            logger.warning("Kubernetes client not installed")

        self.project_root = Path(__file__).parent.parent.parent
        self.local_logs_dir = self.project_root / ".openuba" / "logs"

    def get_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        '''
        Fetch recent logs from all available sources
        Returns list of {id, timestamp, component, level, message}
        '''
        logs = []
        
        if self.k8s_available:
            logs.extend(self._get_k8s_logs(limit))
        
        # Always try to fetch local file logs if K8s fetch didn't yield much (or to supplement)
        # Actually, if we are running 'dev-backend', we might want local file logs PREFERRED for backend/frontend
        # But user asked for "infra pods", implying the K8s ones.
        # Let's mix them if available, but deduplicate logic is hard without unique IDs.
        # Simpler: If K8s available, use it (assuming full cluster). If not, use local files.
        
        if not logs and self.local_logs_dir.exists():
            logs.extend(self._get_local_file_logs(limit))
            
        # Sort by timestamp desc and limit
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        return logs[:limit]

    def _get_k8s_logs(self, limit: int) -> List[Dict[str, Any]]:
        from kubernetes import client
        v1 = client.CoreV1Api()
        logs = []
        
        # Components to look for
        components = ['backend', 'frontend', 'postgres', 'spark-master', 'elasticsearch']
        namespace = os.getenv("KUBERNETES_NAMESPACE", "openuba")
        
        try:
            # Get pods
            pods = v1.list_namespaced_pod(namespace, label_selector=f"app in ({','.join(components)})")
            
            for pod in pods.items:
                component = pod.metadata.labels.get('app', 'unknown')
                try:
                    container = None
                    if component == 'frontend':
                        container = 'frontend'
                    
                    # Get logs
                    log_data = v1.read_namespaced_pod_log(
                        name=pod.metadata.name,
                        namespace=namespace,
                        tail_lines=limit // len(components) + 5, # distribute limit roughly
                        timestamps=True,
                        container=container
                    )
                    
                    parsed = self._parse_k8s_logs(log_data, component)
                    logs.extend(parsed)
                except Exception as e:
                    logger.warning(f"Failed to read logs for pod {pod.metadata.name}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to list pods: {e}")
            self.k8s_available = False # Disable for future calls if listing fails repeatedly?
            
        return logs

    def _parse_k8s_logs(self, log_data: str, component: str) -> List[Dict[str, Any]]:
        entries = []
        for line in log_data.splitlines():
            if not line: continue
            try:
                # K8s logs with timestamps=True format: "2023-10-27T10:00:00.000Z message..."
                parts = line.split(' ', 1)
                if len(parts) < 2: continue
                
                timestamp = parts[0]
                message = parts[1]
                
                # Simple level detection
                level = 'info'
                lower_msg = message.lower()
                if 'error' in lower_msg or 'exception' in lower_msg:
                    level = 'error'
                elif 'warn' in lower_msg:
                    level = 'warning'
                
                entries.append({
                    'id': f"{component}_{timestamp}", # pseudo-unique
                    'timestamp': timestamp,
                    'component': component,
                    'level': level,
                    'message': message[:200] # truncate
                })
            except:
                pass
        return entries

    def _get_local_file_logs(self, limit: int) -> List[Dict[str, Any]]:
        logs = []
        
        # Helper to find latest log file for a component
        def get_latest_log(prefix: str) -> Optional[Path]:
            candidates = list(self.local_logs_dir.glob(f"{prefix}*.log"))
            if not candidates: return None
            return max(candidates, key=lambda p: p.stat().st_mtime)

        files = {
            'backend': get_latest_log("backend"),
            'frontend': get_latest_log("frontend")
        }
        
        for component, path in files.items():
            if not path or not path.exists(): continue
            
            try:
                # Read last N lines using tail-like approach
                with open(path, 'r', errors='ignore') as f:
                    # simplistic approach: read all lines, take last N
                    # for huge logs this is bad, but for dev it simulates ok
                    lines = f.readlines()[-limit:]
                    
                    for line in lines:
                        # try to find timestamp if available (uvicorn logs have it?)
                        # standard uvicorn: "INFO:     127.0.0.1:56885 - \"GET ...\" 200 OK"
                        # no default timestamp in some uvicorn configs unless formatted
                        timestamp = datetime.fromtimestamp(path.stat().st_mtime).isoformat() # default to file time? No, too generic
                        # Use current time as fallback creates confusion if reading old logs.
                        # Try to regex typical timestamps?
                        # For now, let's just use "now" if we can't parse, or maybe file modification time is okayish for "batch" reading
                        # Better: just use current time for display if missing, as these are "recent" logs
                        timestamp = datetime.now().isoformat()
                        
                        level = 'info'
                        if 'ERROR' in line: level = 'error'
                        elif 'WARN' in line: level = 'warning'
                        
                        logs.append({
                            'id': f"{component}_{hash(line)}",
                            'timestamp': timestamp,
                            'component': component,
                            'level': level,
                            'message': line.strip()[:200]
                        })
            except Exception as e:
                logger.warning(f"Failed to read local log {path}: {e}")
                
        return logs
