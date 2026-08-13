'''
Copyright 2019-Present The OpenUBA Platform Authors
splunk integration

Two directions:
  * INPUT  — run a Splunk search and return events (via the REST export API)
  * OUTPUT — forward anomalies/events to Splunk (via the HTTP Event Collector)

Config comes from constructor args with SPLUNK_* env fallbacks, matching the
ElasticsearchConnector pattern. Nothing here is Splunk-SDK-dependent — it uses
plain `requests`, so it also works unchanged inside the self-contained model
runner container.
'''

import json
import logging
import os
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


def _env_flag(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


class SplunkConnector:
    '''
    connector for Splunk Enterprise / Cloud.

    host      — management REST endpoint, e.g. https://splunk:8089 (for search)
    token     — bearer token for the REST API (preferred), OR
    username/password — basic auth for the REST API
    hec_url   — HTTP Event Collector base, e.g. https://splunk:8088 (for output)
    hec_token — HEC token
    '''

    def __init__(
        self,
        host: Optional[str] = None,
        token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        hec_url: Optional[str] = None,
        hec_token: Optional[str] = None,
        verify_ssl: Optional[bool] = None,
        timeout: int = 60,
    ):
        self.host = (host or os.getenv("SPLUNK_HOST", "")).rstrip("/")
        self.token = token or os.getenv("SPLUNK_TOKEN", "")
        self.username = username or os.getenv("SPLUNK_USERNAME", "")
        self.password = password or os.getenv("SPLUNK_PASSWORD", "")
        self.hec_url = (hec_url or os.getenv("SPLUNK_HEC_URL", "")).rstrip("/")
        self.hec_token = hec_token or os.getenv("SPLUNK_HEC_TOKEN", "")
        if verify_ssl is None:
            verify_ssl = _env_flag("SPLUNK_VERIFY_SSL", True)
        self.verify_ssl = verify_ssl
        self.timeout = timeout

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "SplunkConnector":
        '''build a connector from an integration_settings config dict'''
        return cls(
            host=config.get("host"),
            token=config.get("token"),
            username=config.get("username"),
            password=config.get("password"),
            hec_url=config.get("hec_url"),
            hec_token=config.get("hec_token"),
            verify_ssl=config.get("verify_ssl", True),
        )

    # ── auth ─────────────────────────────────────────────────────────

    def _rest_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _rest_auth(self):
        '''basic auth tuple when no bearer token is configured'''
        if not self.token and self.username:
            return (self.username, self.password)
        return None

    # ── INPUT: search ────────────────────────────────────────────────

    @staticmethod
    def _normalize_query(query: str) -> str:
        '''Splunk searches must start with `search` or a generating command (`|`)'''
        q = (query or "").strip()
        if not q:
            raise ValueError("splunk search query is empty")
        if q.startswith("|") or q.lower().startswith("search "):
            return q
        return f"search {q}"

    def search(
        self,
        query: str,
        earliest_time: str = "-24h",
        latest_time: str = "now",
        max_count: int = 1000,
    ) -> List[Dict[str, Any]]:
        '''
        run a blocking Splunk search via the export endpoint and return the
        list of result rows (each a flat dict of field → value).
        '''
        if not self.host:
            raise ValueError("splunk host not configured")

        url = f"{self.host}/services/search/jobs/export"
        payload = {
            "search": self._normalize_query(query),
            "output_mode": "json",
            "earliest_time": earliest_time,
            "latest_time": latest_time,
            "count": max_count,
        }
        logger.info(f"running splunk search on {self.host} (count<={max_count})")
        resp = requests.post(
            url,
            data=payload,
            headers=self._rest_headers(),
            auth=self._rest_auth(),
            verify=self.verify_ssl,
            timeout=self.timeout,
        )
        if resp.status_code != 200:
            raise ValueError(
                f"splunk search failed ({resp.status_code}): {resp.text[:500]}"
            )

        results: List[Dict[str, Any]] = []
        # the export endpoint streams newline-delimited JSON objects
        for line in resp.text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            row = obj.get("result")
            if isinstance(row, dict):
                results.append(row)
        logger.info(f"splunk search returned {len(results)} rows")
        return results

    # ── OUTPUT: HTTP Event Collector ─────────────────────────────────

    def send_event(
        self,
        event: Dict[str, Any],
        sourcetype: str = "openuba",
        source: str = "openuba",
        index: Optional[str] = None,
    ) -> bool:
        '''forward a single event to Splunk via HEC. returns True on success.'''
        if not self.hec_url or not self.hec_token:
            logger.debug("splunk HEC not configured — skipping event forward")
            return False

        url = f"{self.hec_url}/services/collector/event"
        body: Dict[str, Any] = {
            "event": event,
            "sourcetype": sourcetype,
            "source": source,
        }
        if index:
            body["index"] = index
        try:
            resp = requests.post(
                url,
                data=json.dumps(body),
                headers={"Authorization": f"Splunk {self.hec_token}"},
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                return True
            logger.error(f"splunk HEC send failed ({resp.status_code}): {resp.text[:300]}")
            return False
        except Exception as e:
            logger.error(f"splunk HEC send error: {e}")
            return False

    def send_anomaly(self, anomaly: Dict[str, Any], index: Optional[str] = None) -> bool:
        '''forward an OpenUBA anomaly to Splunk as an openuba:anomaly event'''
        return self.send_event(anomaly, sourcetype="openuba:anomaly", index=index)

    def send_anomalies(self, anomalies: List[Dict[str, Any]], index: Optional[str] = None) -> int:
        '''forward a batch of anomalies; returns the count successfully sent'''
        sent = 0
        for a in anomalies:
            if self.send_anomaly(a, index=index):
                sent += 1
        return sent

    # ── connectivity ─────────────────────────────────────────────────

    def test_connection(self) -> Dict[str, Any]:
        '''probe the REST management endpoint (or HEC if only that is set)'''
        try:
            if self.host:
                resp = requests.get(
                    f"{self.host}/services/server/info",
                    params={"output_mode": "json"},
                    headers=self._rest_headers(),
                    auth=self._rest_auth(),
                    verify=self.verify_ssl,
                    timeout=10,
                )
                if resp.status_code == 200:
                    version = ""
                    try:
                        entries = resp.json().get("entry", [])
                        if entries:
                            version = entries[0].get("content", {}).get("version", "")
                    except Exception:
                        pass
                    return {"status": "connected", "version": version}
                return {"status": "error", "message": f"HTTP {resp.status_code}"}

            if self.hec_url and self.hec_token:
                resp = requests.get(
                    f"{self.hec_url}/services/collector/health",
                    headers={"Authorization": f"Splunk {self.hec_token}"},
                    verify=self.verify_ssl,
                    timeout=10,
                )
                if resp.status_code == 200:
                    return {"status": "connected", "channel": "hec"}
                return {"status": "error", "message": f"HEC HTTP {resp.status_code}"}

            return {"status": "error", "message": "host or hec_url not configured"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
