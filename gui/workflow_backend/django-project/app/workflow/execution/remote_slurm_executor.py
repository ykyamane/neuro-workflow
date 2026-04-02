"""Remote execution backend — submits jobs to a Slurm cluster over SSH."""

from __future__ import annotations

import logging
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from django.conf import settings

from .base import ExecutionBackend, ExecutionResult, ExecutionStatus

logger = logging.getLogger(__name__)

_SLURM_STATE_MAP = {
    "PENDING": ExecutionStatus.PENDING,
    "RUNNING": ExecutionStatus.RUNNING,
    "COMPLETING": ExecutionStatus.RUNNING,
    "COMPLETED": ExecutionStatus.COMPLETED,
    "FAILED": ExecutionStatus.FAILED,
    "TIMEOUT": ExecutionStatus.FAILED,
    "CANCELLED": ExecutionStatus.CANCELLED,
    "NODE_FAIL": ExecutionStatus.FAILED,
    "OUT_OF_MEMORY": ExecutionStatus.FAILED,
}


def _ssh_cmd(host: str, user: str, cmd: str, key_path: Optional[str] = None) -> str:
    """Run a command on a remote host via SSH and return stdout."""
    ssh_args = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes"]
    if key_path:
        ssh_args += ["-i", key_path]
    ssh_args += [f"{user}@{host}", cmd]
    result = subprocess.run(ssh_args, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(
            f"SSH command failed (rc={result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout.strip()


def _rsync(
    src: str,
    dst: str,
    host: str,
    user: str,
    key_path: Optional[str] = None,
    to_remote: bool = True,
) -> None:
    """rsync files to/from the remote host."""
    rsync_args = ["rsync", "-az", "--mkpath"]
    if key_path:
        rsync_args += ["-e", f"ssh -i {key_path} -o StrictHostKeyChecking=no"]
    else:
        rsync_args += ["-e", "ssh -o StrictHostKeyChecking=no"]
    if to_remote:
        rsync_args += [src, f"{user}@{host}:{dst}"]
    else:
        rsync_args += [f"{user}@{host}:{src}", dst]
    subprocess.run(rsync_args, check=True, capture_output=True, text=True, timeout=120)


class RemoteSlurmExecutor(ExecutionBackend):
    """Submit workflow scripts to a Slurm cluster via SSH.

    Configuration is read from environment variables:
      SLURM_HOST          – hostname or IP of the login node
      SLURM_USER          – SSH user
      SLURM_SSH_KEY       – path to private key (optional, uses ssh-agent otherwise)
      SLURM_REMOTE_DIR    – remote working directory (default: ~/neuroworkflow-runs)
      SLURM_PARTITION      – Slurm partition (optional)
      SLURM_ACCOUNT        – Slurm account (optional)
    """

    def __init__(self):
        self.host = os.getenv("SLURM_HOST", "")
        self.user = os.getenv("SLURM_USER", "")
        self.key_path = os.getenv("SLURM_SSH_KEY") or None
        self.remote_dir = os.getenv("SLURM_REMOTE_DIR", "~/neuroworkflow-runs")
        self.partition = os.getenv("SLURM_PARTITION", "")
        self.account = os.getenv("SLURM_ACCOUNT", "")
        self.local_staging = Path(settings.BASE_DIR) / "run_staging"
        self.local_staging.mkdir(parents=True, exist_ok=True)

    def _ssh(self, cmd: str) -> str:
        return _ssh_cmd(self.host, self.user, cmd, self.key_path)

    def _sync_to_remote(self, local: str, remote: str) -> None:
        _rsync(local, remote, self.host, self.user, self.key_path, to_remote=True)

    def _sync_from_remote(self, remote: str, local: str) -> None:
        _rsync(remote, local, self.host, self.user, self.key_path, to_remote=False)

    # ── Interface implementation ───────────────────────────────────────

    def submit(
        self,
        workflow_id: str,
        project_name: str,
        code: str,
        *,
        resource_requests: Optional[dict] = None,
    ) -> ExecutionResult:
        result = ExecutionResult(
            status=ExecutionStatus.PENDING,
            submitted_at=datetime.now(timezone.utc),
        )
        run_id = result.run_id
        remote_run_dir = f"{self.remote_dir}/{run_id}"

        local_dir = self.local_staging / run_id
        local_dir.mkdir(parents=True, exist_ok=True)

        script_name = f"{project_name}.py"
        (local_dir / script_name).write_text(code)

        rr = resource_requests or {}
        sbatch_lines = [
            "#!/bin/bash",
            f"#SBATCH --job-name=nw-{project_name[:20]}",
            f"#SBATCH --output={remote_run_dir}/slurm-%j.out",
            f"#SBATCH --error={remote_run_dir}/slurm-%j.err",
        ]
        if self.partition:
            sbatch_lines.append(f"#SBATCH --partition={self.partition}")
        if self.account:
            sbatch_lines.append(f"#SBATCH --account={self.account}")
        if rr.get("nodes"):
            sbatch_lines.append(f"#SBATCH --nodes={rr['nodes']}")
        if rr.get("ntasks"):
            sbatch_lines.append(f"#SBATCH --ntasks={rr['ntasks']}")
        if rr.get("cpus_per_task"):
            sbatch_lines.append(f"#SBATCH --cpus-per-task={rr['cpus_per_task']}")
        if rr.get("mem"):
            sbatch_lines.append(f"#SBATCH --mem={rr['mem']}")
        if rr.get("time"):
            sbatch_lines.append(f"#SBATCH --time={rr['time']}")
        if rr.get("gres"):
            sbatch_lines.append(f"#SBATCH --gres={rr['gres']}")

        sbatch_lines += [
            "",
            f"cd {remote_run_dir}",
            f"python {script_name} > stdout.log 2> stderr.log",
            "echo $? > exit_code.txt",
        ]
        (local_dir / "run.sbatch").write_text("\n".join(sbatch_lines) + "\n")

        try:
            self._ssh(f"mkdir -p {remote_run_dir}")
            self._sync_to_remote(f"{local_dir}/", remote_run_dir + "/")
            output = self._ssh(f"cd {remote_run_dir} && sbatch run.sbatch")
            match = re.search(r"Submitted batch job (\d+)", output)
            if match:
                result.remote_job_id = match.group(1)
                result.status = ExecutionStatus.PENDING
            else:
                result.status = ExecutionStatus.FAILED
                result.error = f"sbatch output not recognized: {output}"
        except Exception as exc:
            logger.exception("Failed to submit Slurm job for run %s", run_id)
            result.status = ExecutionStatus.FAILED
            result.error = str(exc)

        return result

    def get_status(self, run_id: str) -> ExecutionResult:
        result = ExecutionResult(run_id=run_id)

        meta = self._read_remote_meta(run_id)
        job_id = meta.get("job_id")
        if not job_id:
            result.status = ExecutionStatus.FAILED
            result.error = "No remote job ID found"
            return result
        result.remote_job_id = job_id

        try:
            out = self._ssh(
                f"sacct -j {job_id} --format=State --noheader --parsable2 | head -1"
            )
            state = out.strip().split("+")[0].upper() if out.strip() else ""
            result.status = _SLURM_STATE_MAP.get(state, ExecutionStatus.RUNNING)
        except Exception as exc:
            logger.warning("sacct failed for job %s: %s", job_id, exc)
            result.status = ExecutionStatus.RUNNING

        if result.status in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED):
            remote_run_dir = f"{self.remote_dir}/{run_id}"
            try:
                result.exit_code = int(
                    self._ssh(f"cat {remote_run_dir}/exit_code.txt").strip()
                )
            except Exception:
                pass
            try:
                result.stdout = self._ssh(f"cat {remote_run_dir}/stdout.log")
            except Exception:
                pass
            try:
                result.stderr = self._ssh(f"cat {remote_run_dir}/stderr.log")
            except Exception:
                pass

        return result

    def get_logs(self, run_id: str) -> str:
        remote_run_dir = f"{self.remote_dir}/{run_id}"
        parts = []
        for f in ("stdout.log", "stderr.log"):
            try:
                content = self._ssh(f"cat {remote_run_dir}/{f} 2>/dev/null || true")
                if content:
                    parts.append(content)
            except Exception:
                pass
        try:
            slurm_out = self._ssh(
                f"cat {remote_run_dir}/slurm-*.out 2>/dev/null || true"
            )
            if slurm_out:
                parts.append(slurm_out)
        except Exception:
            pass
        return "\n".join(parts)

    def cancel(self, run_id: str) -> bool:
        meta = self._read_remote_meta(run_id)
        job_id = meta.get("job_id")
        if not job_id:
            return False
        try:
            self._ssh(f"scancel {job_id}")
            return True
        except Exception as exc:
            logger.warning("scancel failed for job %s: %s", job_id, exc)
            return False

    # ── Helpers ────────────────────────────────────────────────────────

    def _read_remote_meta(self, run_id: str) -> dict:
        """Read metadata from the local staging area for this run."""
        local_dir = self.local_staging / run_id
        meta: dict = {}
        meta_file = local_dir / "meta.json"
        if meta_file.exists():
            import json
            meta = json.loads(meta_file.read_text())
        return meta
