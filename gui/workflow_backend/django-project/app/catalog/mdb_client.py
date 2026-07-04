"""HTTP client for the mdb metadata catalog service."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

DEFAULT_MDB_BASE_URL = "http://host.docker.internal:8004"
DEFAULT_TIMEOUT = 30.0
VALID_SOURCES = frozenset({"dandi", "cbs", "brainminds", "bmb_human", "aws"})


class MDBClientError(Exception):
    """Raised when mdb returns an error or is unreachable."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class MDBClient:
    """Thin proxy client for mdb Flask API (streamlined_web_interface)."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        raw = (base_url or os.getenv("MDB_BASE_URL") or DEFAULT_MDB_BASE_URL).strip()
        self.base_url = raw.rstrip("/")
        self.timeout = timeout

    def is_configured(self) -> bool:
        return bool(self.base_url)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.is_configured():
            raise MDBClientError("MDB_BASE_URL is not configured")

        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(method, url, params=params, json=json_body)
        except httpx.RequestError as exc:
            logger.warning("mdb request failed: %s %s", method, url, exc_info=True)
            raise MDBClientError(f"mdb unreachable at {self.base_url}: {exc}") from exc

        if response.status_code >= 400:
            detail = response.text[:500]
            raise MDBClientError(
                f"mdb error {response.status_code} for {path}: {detail}",
                status_code=response.status_code,
            )

        try:
            return response.json()
        except ValueError as exc:
            raise MDBClientError(f"mdb returned non-JSON from {path}") from exc

    def search_datasets(
        self,
        query: str,
        source: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"q": query}
        if source:
            params["source"] = source
        data = self._request("GET", "/api/search_api_datasets", params=params)
        return data.get("datasets", [])

    def list_datasets(
        self,
        source: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"limit": limit}
        if source:
            params["source"] = source
        data = self._request("GET", "/api/api_datasets", params=params)
        return data.get("datasets", [])

    def get_dataset(
        self,
        source: str,
        dataset_id: str,
        *,
        scan_limit: int = 2000,
    ) -> Optional[Dict[str, Any]]:
        """Resolve a dataset by ID (mdb has no per-ID endpoint)."""
        datasets = self.list_datasets(source=source, limit=scan_limit)
        for dataset in datasets:
            if str(dataset.get("dataset_id")) == str(dataset_id):
                return dataset
        return None

    def get_statistics(self) -> Dict[str, Any]:
        return self._request("GET", "/api/api_statistics")

    def sync_all(self) -> Dict[str, Any]:
        return self._request("POST", "/api/sync_apis")


def normalize_dataset(
    raw: Dict[str, Any],
    *,
    include_data_urls: bool = False,
    include_metadata: bool = False,
) -> Dict[str, Any]:
    """Map mdb api_datasets row to neuro-workflow catalog shape."""
    metadata = raw.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {}

    data_urls = metadata.get("data_urls") or []
    summary = metadata.get("data_url_summary") or {}

    normalized: Dict[str, Any] = {
        "source": raw.get("source"),
        "dataset_id": raw.get("dataset_id"),
        "name": raw.get("name"),
        "description": raw.get("description"),
        "synced_at": raw.get("synced_at"),
        "data_url_count": summary.get("count", len(data_urls)),
        "data_url_total": summary.get("total_count"),
        "truncated": bool(summary.get("truncated")),
        "landing_page": metadata.get("landing_page"),
    }

    if include_data_urls:
        normalized["data_urls"] = data_urls
    if include_metadata:
        normalized["metadata"] = metadata

    return normalized


def get_mdb_client() -> MDBClient:
    return MDBClient()
