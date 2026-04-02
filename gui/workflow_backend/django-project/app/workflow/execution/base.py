"""Abstract execution backend for running workflow scripts."""

from __future__ import annotations

import enum
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class ExecutionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionResult:
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: ExecutionStatus = ExecutionStatus.PENDING
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None
    submitted_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    remote_job_id: Optional[str] = None
    artifacts: dict = field(default_factory=dict)


class ExecutionBackend(ABC):
    """Interface for submitting and tracking workflow runs."""

    @abstractmethod
    def submit(
        self,
        workflow_id: str,
        project_name: str,
        code: str,
        *,
        resource_requests: Optional[dict] = None,
    ) -> ExecutionResult:
        """Submit a workflow run. Returns immediately with a pending result."""
        ...

    @abstractmethod
    def get_status(self, run_id: str) -> ExecutionResult:
        """Poll the status of a previously submitted run."""
        ...

    @abstractmethod
    def get_logs(self, run_id: str) -> str:
        """Return combined stdout+stderr collected so far."""
        ...

    @abstractmethod
    def cancel(self, run_id: str) -> bool:
        """Attempt to cancel a running job. Returns True if cancelled."""
        ...
