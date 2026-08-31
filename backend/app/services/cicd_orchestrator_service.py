"""
CI/CD Pipeline Orchestration service module.
Handles DAG pipeline execution, artifact metadata management, and dynamic deployment strategies.
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
class Artifact:
    artifact_id: str
    name: str
    version: str
    download_url: str
    environment: str = "build"  # e.g., build, staging, production
    created_at: float = field(default_factory=time.time)


@dataclass
class PipelineJob:
    job_id: str
    name: str
    command: str
    depends_on: List[str] = field(default_factory=list) # IDs of jobs that must pass first
    status: PipelineStatus = PipelineStatus.PENDING
    exit_code: Optional[int] = None
    stdout_log: str = ""
    stderr_log: str = ""


@dataclass
class PipelineStage:
    stage_id: str
    name: str
    jobs: List[PipelineJob] = field(default_factory=list)


@dataclass
class Pipeline:
    pipeline_id: str
    project_id: str
    commit_sha: str
    branch: str = "main"
    stages: List[PipelineStage] = field(default_factory=list)
    status: PipelineStatus = PipelineStatus.PENDING
    created_at: float = field(default_factory=time.time)


class DeploymentStrategy:
    """Abstract deployment strategy plugin."""
    def execute(self, artifact: Artifact, target_env: str) -> bool:
        raise NotImplementedError


class BlueGreenDeployment(DeploymentStrategy):
    def execute(self, artifact: Artifact, target_env: str) -> bool:
        # Simulated blue-green deployment
        print(f"Deploying {artifact.name} v{artifact.version} to inactive green environment...")
        print("Running smoke tests on green environment...")
        print("Swapping router traffic from blue to green...")
        return True


class CanaryDeployment(DeploymentStrategy):
    def __init__(self, traffic_percentages: List[int] = [10, 50, 100]):
        self.traffic_percentages = traffic_percentages

    def execute(self, artifact: Artifact, target_env: str) -> bool:
        # Simulated canary rollout
        for percent in self.traffic_percentages:
            print(f"Routing {percent}% of traffic to canary nodes running v{artifact.version}...")
            time.sleep(0.01) # Simulate health check dwell time
        return True


class RollingDeployment(DeploymentStrategy):
    def execute(self, artifact: Artifact, target_env: str) -> bool:
        print(f"Executing rolling deployment of v{artifact.version} across all nodes...")
        return True


class CICDOrchestratorService:
    """Service to parse, manage, and evaluate DAG-based CI/CD pipelines."""

    def __init__(self):
        self._pipelines: Dict[str, Pipeline] = {}
        self._artifacts: Dict[str, Artifact] = {}

    def create_pipeline(self, project_id: str, commit_sha: str, branch: str, stages_def: List[Dict[str, Any]]) -> Pipeline:
        """Constructs a new pipeline based on a YAML-like dictionary definition."""
        pipeline_id = f"pipe_{project_id}_{int(time.time())}_{commit_sha[:7]}"
        
        stages = []
        for stage_idx, s_def in enumerate(stages_def):
            stage_id = f"stage_{stage_idx}"
            jobs = []
            for j_def in s_def.get("jobs", []):
                jobs.append(PipelineJob(
                    job_id=j_def["id"],
                    name=j_def.get("name", "Unnamed Job"),
                    command=j_def.get("run", ""),
                    depends_on=j_def.get("depends_on", [])
                ))
            stages.append(PipelineStage(stage_id=stage_id, name=s_def.get("name", "Unnamed Stage"), jobs=jobs))

        pipeline = Pipeline(
            pipeline_id=pipeline_id,
            project_id=project_id,
            commit_sha=commit_sha,
            branch=branch,
            stages=stages,
            status=PipelineStatus.PENDING
        )
        self._pipelines[pipeline_id] = pipeline
        return pipeline

    def handle_webhook_trigger(self, provider: str, payload: Dict[str, Any]) -> Optional[Pipeline]:
        """Translates external webhook payloads (GitHub/GitLab) into an internal pipeline."""
        if provider == "github":
            # Very basic extraction mapping
            return self.create_pipeline(
                project_id=payload.get("repository", {}).get("name", "unknown"),
                commit_sha=payload.get("after", "unknown"),
                branch=payload.get("ref", "refs/heads/main").split("/")[-1],
                stages_def=[{"name": "Build", "jobs": [{"id": "build", "run": "make"}]}]
            )
        elif provider == "gitlab":
            return self.create_pipeline(
                project_id=payload.get("project", {}).get("path_with_namespace", "unknown"),
                commit_sha=payload.get("checkout_sha", "unknown"),
                branch=payload.get("ref", "refs/heads/main").split("/")[-1],
                stages_def=[{"name": "Build", "jobs": [{"id": "build", "run": "make"}]}]
            )
        return None

    def resolve_next_jobs(self, pipeline_id: str) -> List[PipelineJob]:
        """Returns the list of jobs in the DAG that are eligible to run immediately."""
        pipeline = self._pipelines.get(pipeline_id)
        if not pipeline or pipeline.status in [PipelineStatus.FAILED, PipelineStatus.CANCELLED]:
            return []

        # Flatten all jobs to map ID to Job object
        job_map = {}
        for stage in pipeline.stages:
            for job in stage.jobs:
                job_map[job.job_id] = job

        eligible_jobs = []
        for stage in pipeline.stages:
            for job in stage.jobs:
                if job.status == PipelineStatus.PENDING:
                    # Check if all dependencies have PASSED
                    deps_met = True
                    for dep_id in job.depends_on:
                        dep_job = job_map.get(dep_id)
                        if not dep_job or dep_job.status != PipelineStatus.PASSED:
                            deps_met = False
                            break
                    if deps_met:
                        eligible_jobs.append(job)

        return eligible_jobs

    def record_job_result(
        self, pipeline_id: str, job_id: str, exit_code: int, stdout: str = "", stderr: str = ""
    ) -> Optional[Pipeline]:
        """Records a job execution and propagates status through the DAG."""
        pipeline = self._pipelines.get(pipeline_id)
        if not pipeline:
            return None

        job_found = None
        for stage in pipeline.stages:
            for job in stage.jobs:
                if job.job_id == job_id:
                    job_found = job
                    break

        if not job_found:
            return None

        job_found.exit_code = exit_code
        job_found.stdout_log = stdout
        job_found.stderr_log = stderr
        job_found.status = PipelineStatus.PASSED if exit_code == 0 else PipelineStatus.FAILED

        if job_found.status == PipelineStatus.FAILED:
            # Propagate SKIPPED status to any job that depends on this failed job
            self._propagate_skip(pipeline, job_found.job_id)

        self._evaluate_pipeline_status(pipeline)
        return pipeline

    def _propagate_skip(self, pipeline: Pipeline, failed_job_id: str):
        """Recursively marks dependent jobs as SKIPPED if their parent fails."""
        skipped_any = False
        for stage in pipeline.stages:
            for job in stage.jobs:
                if job.status == PipelineStatus.PENDING and failed_job_id in job.depends_on:
                    job.status = PipelineStatus.SKIPPED
                    skipped_any = True
                    # Recurse to skip children of this newly skipped job
                    self._propagate_skip(pipeline, job.job_id)

    def _evaluate_pipeline_status(self, pipeline: Pipeline) -> None:
        """Determines if the entire pipeline is finished."""
        all_terminal = True
        any_failed = False
        
        for stage in pipeline.stages:
            for job in stage.jobs:
                if job.status in [PipelineStatus.PENDING, PipelineStatus.RUNNING]:
                    all_terminal = False
                if job.status == PipelineStatus.FAILED:
                    any_failed = True

        if all_terminal:
            pipeline.status = PipelineStatus.FAILED if any_failed else PipelineStatus.PASSED
        else:
            pipeline.status = PipelineStatus.RUNNING

    # --- Artifact Management ---
    
    def publish_artifact(self, name: str, version: str, download_url: str) -> Artifact:
        art_id = f"art_{name}_{version}_{int(time.time())}"
        artifact = Artifact(artifact_id=art_id, name=name, version=version, download_url=download_url)
        self._artifacts[art_id] = artifact
        return artifact

    def promote_artifact(self, artifact_id: str, new_environment: str, strategy: DeploymentStrategy) -> bool:
        artifact = self._artifacts.get(artifact_id)
        if not artifact:
            return False
            
        success = strategy.execute(artifact, new_environment)
        if success:
            artifact.environment = new_environment
            return True
        return False


cicd_orchestrator_service = CICDOrchestratorService()
