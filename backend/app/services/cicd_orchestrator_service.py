"""
CI/CD Pipeline Orchestration service module.
Handles pipeline parsing, DAG stage resolution, step execution tracking, and status evaluation.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import time


class PipelineStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


@dataclass
class PipelineStep:
    name: str
    command: str
    status: PipelineStatus = PipelineStatus.PENDING
    exit_code: Optional[int] = None
    duration_seconds: float = 0.0
    stdout_log: str = ""
    stderr_log: str = ""


@dataclass
class PipelineJob:
    job_id: str
    project_id: str
    commit_sha: str
    branch: str = "main"
    steps: List[PipelineStep] = field(default_factory=list)
    status: PipelineStatus = PipelineStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


class CICDOrchestratorService:
    """Service to parse, manage, and evaluate CI/CD pipeline job lifecycles."""

    def __init__(self):
        self._jobs: Dict[str, PipelineJob] = {}

    def create_job(
        self, project_id: str, commit_sha: str, step_commands: List[Dict[str, str]], branch: str = "main"
    ) -> PipelineJob:
        """Constructs a new pipeline job with initialized steps."""
        job_id = f"job_{project_id}_{int(time.time())}_{commit_sha[:7]}"
        steps = [
            PipelineStep(
                name=step.get("name", f"step-{i+1}"),
                command=step.get("run", "")
            )
            for i, step in enumerate(step_commands)
        ]
        job = PipelineJob(
            job_id=job_id,
            project_id=project_id,
            commit_sha=commit_sha,
            branch=branch,
            steps=steps,
            status=PipelineStatus.PENDING
        )
        self._jobs[job_id] = job
        return job

    def start_job(self, job_id: str) -> Optional[PipelineJob]:
        """Transitions job status to running."""
        job = self._jobs.get(job_id)
        if job and job.status == PipelineStatus.PENDING:
            job.status = PipelineStatus.RUNNING
            job.started_at = time.time()
        return job

    def record_step_result(
        self, job_id: str, step_index: int, exit_code: int, duration: float, stdout: str = "", stderr: str = ""
    ) -> Optional[PipelineJob]:
        """Records the execution result of a single step."""
        job = self._jobs.get(job_id)
        if not job or step_index < 0 or step_index >= len(job.steps):
            return None

        step = job.steps[step_index]
        step.exit_code = exit_code
        step.duration_seconds = duration
        step.stdout_log = stdout
        step.stderr_log = stderr
        step.status = PipelineStatus.PASSED if exit_code == 0 else PipelineStatus.FAILED

        self.evaluate_job_status(job)
        return job

    def evaluate_job_status(self, job: PipelineJob) -> PipelineStatus:
        """Evaluates overall job status based on individual step statuses."""
        if any(s.status == PipelineStatus.FAILED for s in job.steps):
            job.status = PipelineStatus.FAILED
            job.completed_at = time.time()
        elif all(s.status == PipelineStatus.PASSED for s in job.steps):
            job.status = PipelineStatus.PASSED
            job.completed_at = time.time()
        elif any(s.status == PipelineStatus.RUNNING for s in job.steps):
            job.status = PipelineStatus.RUNNING
        return job.status

    def get_job(self, job_id: str) -> Optional[PipelineJob]:
        return self._jobs.get(job_id)


cicd_orchestrator_service = CICDOrchestratorService()
