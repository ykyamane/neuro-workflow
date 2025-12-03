import re
import os
import json
from pathlib import Path
from django.conf import settings
from .models import FlowProject, FlowNode, FlowEdge
import logging
import traceback
import subprocess

logger = logging.getLogger(__name__)

class RunWorkflowService:
    """A service that run the Python code generated from the workflow"""

    def __init__(self):
        self.code_dir = Path(settings.BASE_DIR) / "codes/projects"
        self.code_dir.mkdir(exist_ok=True)

    def run_workflow_code(self, workflow_id, project_name):
        script_path = self.code_dir / str(project_name) / f"{project_name}.py"

        logger.info(f"DEBUG: Run Workflow [{project_name}: {script_path}]")

        try:
            result = subprocess.run(
                ["python", script_path],
                capture_output=True,
                text=True,
                check=True
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        except subprocess.CalledProcessError as e:
            return {
                "error": str(e),
                "stdout": e.stdout,
                "stderr": e.stderr,
            }

