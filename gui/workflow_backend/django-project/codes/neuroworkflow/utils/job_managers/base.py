"""
Base classes for job manager implementations.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from ...core.schema import ResourceRequirements


class JobStatus(Enum):
    """Status of a submitted job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


@dataclass
class JobInfo:
    """Information about a submitted job."""
    job_id: str
    status: JobStatus
    submitted_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    output_path: Optional[str] = None
    log_path: Optional[str] = None


class JobManager(ABC):
    """
    Abstract base class for job managers.
    
    Job managers handle submission and monitoring of workflows on HPC systems.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize job manager.
        
        Args:
            config: Configuration dictionary (implementation-specific)
        """
        self.config = config or {}
    
    @abstractmethod
    def generate_job_script(
        self,
        python_script: str,
        resources: ResourceRequirements,
        job_name: str,
        output_dir: str = "./output",
        additional_args: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate job submission script.
        
        Args:
            python_script: Python script to execute
            resources: Resource requirements
            job_name: Name for the job
            output_dir: Output directory for job files
            additional_args: Additional job-specific arguments
        
        Returns:
            Path to generated job script
        """
        pass
    
    @abstractmethod
    def submit_job(self, job_script_path: str) -> str:
        """
        Submit job to the scheduler.
        
        Args:
            job_script_path: Path to job submission script
        
        Returns:
            Job ID assigned by the scheduler
        """
        pass
    
    @abstractmethod
    def get_job_status(self, job_id: str) -> JobStatus:
        """
        Get current status of a job.
        
        Args:
            job_id: Job ID returned by submit_job()
        
        Returns:
            Current job status
        """
        pass
    
    @abstractmethod
    def get_job_info(self, job_id: str) -> JobInfo:
        """
        Get detailed information about a job.
        
        Args:
            job_id: Job ID
        
        Returns:
            Job information
        """
        pass
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job.
        
        Args:
            job_id: Job ID to cancel
        
        Returns:
            True if cancellation was successful
        """
        # Default implementation - override in subclasses
        raise NotImplementedError(f"Job cancellation not implemented for {self.__class__.__name__}")
    
    def get_job_output(self, job_id: str) -> Optional[str]:
        """
        Get path to job output file.
        
        Args:
            job_id: Job ID
        
        Returns:
            Path to output file, or None if not available
        """
        job_info = self.get_job_info(job_id)
        return job_info.output_path
    
    def get_job_logs(self, job_id: str) -> Optional[str]:
        """
        Get path to job log file.
        
        Args:
            job_id: Job ID
        
        Returns:
            Path to log file, or None if not available
        """
        job_info = self.get_job_info(job_id)
        return job_info.log_path

