"""
CUSTOM_API Adapter — configurable HTTP passthrough to any external KB API.

Key behaviors:
    query()      — GET/POST to configured endpoint
    populate()   → POST to configured endpoint; FAILURE = hard ConfigError halt
    scan_gaps()  — GET to scan_gaps endpoint

CUSTOM_API populate() failure rule:
    populate() failures are hard ConfigError halts, not silent skips.
    If the API returns non-2xx or a network error occurs, ConfigError is raised.
    This is intentional — CUSTOM_API callers must ensure the API is reliable
    before using populate().

CALLER_INVARIANCE: import this only from AdapterSession (session.py).
"""

import json
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone

from ..interface import BaseAdapter, QueryResult, PopulateResult, GapResult
from ..errors import AdapterIOError, ConfigError


class CustomApiAdapter(BaseAdapter):
    """
    KB adapter backed by a configurable external HTTP API.

    Connection config fields:
        base_url       — API base URL (required)
        query_path     — path for query endpoint (default: "/query")
        populate_path  — path for populate endpoint (default: "/populate")
        scan_gaps_path — path for scan_gaps endpoint (default: "/scan_gaps")
        api_key        — API key header value (optional)
        api_key_header — Header name for API key (default: "X-API-Key")
        method         — HTTP method for query (default: "POST")
        timeout        — per-call timeout in seconds (default: 60)

    populate() failure behavior:
        Non-2xx response or network error → ConfigError (recoverable: False)
        This is a HARD HALT — not silent skip.
    """

    def __init__(self, connection_config: dict):
        super().__init__("CUSTOM_API", connection_config)
        base_url = connection_config.get("base_url")
        if not base_url:
            raise ConfigError(
                "CUSTOM_API adapter requires 'base_url' in connection config",
                offending_field="kb_adapter.connection.base_url",
                adapter_type="CUSTOM_API",
            )
        self._base_url = base_url.rstrip("/")
        self._query_path = connection_config.get("query_path", "/query")
        self._populate_path = connection_config.get("populate_path", "/populate")
        self._scan_gaps_path = connection_config.get("scan_gaps_path", "/scan_gaps")
        self._api_key = connection_config.get("api_key")
        self._api_key_header = connection_config.get("api_key_header", "X-API-Key")
        self._method = connection_config.get("method", "POST").upper()
        self._timeout = connection_config.get("timeout", 60)

    def _make_headers(self) -> dict:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._api_key:
            headers[self._api_key_header] = self._api_key
        return headers

    def _http_request(self, path: str, body: dict, method: str = None) -> dict:
        """
        Make an HTTP request and return parsed JSON response.

        Raises:
            AdapterIOError: network error, timeout, or unexpected status
        """
        url = self._base_url + path
        http_method = (method or self._method).upper()
        payload = json.dumps(body).encode("utf-8")
        headers = self._make_headers()

        req = urllib.request.Request(url, data=payload, headers=headers, method=http_method)

        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                status = resp.getcode()
                raw = resp.read().decode("utf-8")
                try:
                    return {"status": status, "body": json.loads(raw)}
                except json.JSONDecodeError:
                    return {"status": status, "body": {"raw": raw}}
        except urllib.error.HTTPError as e:
            return {"status": e.code, "body": {"error": str(e)}}
        except urllib.error.URLError as e:
            raise AdapterIOError(
                f"CUSTOM_API network error calling '{url}': {e.reason}",
                adapter_type="CUSTOM_API",
            )
        except TimeoutError:
            raise AdapterIOError(
                f"CUSTOM_API request to '{url}' timed out after {self._timeout}s",
                adapter_type="CUSTOM_API",
            )

    def query(self, query_string: str, filters: dict = None) -> list:
        """
        Query the external API.

        Returns:
            list of QueryResult objects

        Raises:
            AdapterIOError: network error, timeout, or non-2xx response
        """
        body = {"query": query_string, "filters": filters or {}}
        resp = self._http_request(self._query_path, body)
        status = resp["status"]

        if status < 200 or status >= 300:
            raise AdapterIOError(
                f"CUSTOM_API query returned HTTP {status} from '{self._base_url}{self._query_path}'",
                adapter_type="CUSTOM_API",
            )

        results_raw = resp["body"].get("results", [])
        return [
            QueryResult(
                entry_id=r.get("entry_id", ""),
                content=r.get("content", ""),
                metadata=r.get("metadata", {}),
                source_adapter="CUSTOM_API",
            )
            for r in results_raw
        ]

    def populate(self, content: str, tier: int, metadata: dict = None) -> PopulateResult:
        """
        POST content to the external API.

        FAILURE = hard ConfigError halt (not silent skip).
        Non-2xx or network error raises ConfigError(recoverable=False).

        Returns:
            PopulateResult(kind="write_status") — callers MUST check .kind

        Raises:
            ConfigError: non-2xx response or network failure (hard halt)
        """
        body = {
            "content": content,
            "tier": tier,
            "metadata": metadata or {},
        }

        try:
            resp = self._http_request(self._populate_path, body, method="POST")
        except AdapterIOError as e:
            # Escalate to ConfigError (hard halt) per CUSTOM_API spec
            raise ConfigError(
                f"CUSTOM_API populate() network failure (hard halt): {e.args[0]}. "
                "Fix connectivity or switch adapter_type before retrying.",
                offending_field="kb_adapter.connection.base_url",
                adapter_type="CUSTOM_API",
            )

        status = resp["status"]
        if status < 200 or status >= 300:
            # Hard halt — NOT silent skip
            raise ConfigError(
                f"CUSTOM_API populate() returned HTTP {status} — hard halt. "
                f"URL: {self._base_url}{self._populate_path}. "
                "Fix API endpoint or switch adapter_type before retrying.",
                offending_field="kb_adapter.connection.base_url",
                adapter_type="CUSTOM_API",
            )

        body_resp = resp["body"]
        return PopulateResult(
            kind="write_status",
            success=body_resp.get("success", True),
            written_count=body_resp.get("written_count", 1),
            errors=body_resp.get("errors", []),
        )

    def scan_gaps(self, schema_definition: dict) -> list:
        """
        POST schema_definition to the external scan_gaps endpoint.

        Returns:
            list of GapResult objects

        Raises:
            AdapterIOError: network error, timeout, or non-2xx response
        """
        body = {"schema_definition": schema_definition}
        resp = self._http_request(self._scan_gaps_path, body, method="POST")
        status = resp["status"]

        if status < 200 or status >= 300:
            raise AdapterIOError(
                f"CUSTOM_API scan_gaps returned HTTP {status} from '{self._base_url}{self._scan_gaps_path}'",
                adapter_type="CUSTOM_API",
            )

        gaps_raw = resp["body"].get("gaps", [])
        gaps = []
        for g in gaps_raw:
            try:
                gaps.append(GapResult(
                    gap_id=g["gap_id"],
                    location=g.get("location", ""),
                    gap_type=g.get("type", "missing"),
                    schema_node=g.get("schema_node", {}),
                ))
            except (KeyError, ValueError):
                continue
        return gaps
