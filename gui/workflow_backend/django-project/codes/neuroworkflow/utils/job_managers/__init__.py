"""
Job manager implementations for HPC job submission.

This module provides abstractions for submitting workflows to various
HPC systems and job schedulers (SLURM, PBS, AWS Batch, etc.).
"""

from .base import JobManager, JobStatus
from .slurm import SLURMJobManager

__all__ = ['JobManager', 'JobStatus', 'SLURMJobManager']

