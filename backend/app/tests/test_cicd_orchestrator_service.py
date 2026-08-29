"""
Comprehensive Unit tests for Built-in CI/CD Pipeline Orchestrator.
"""

import pytest
from app.services.cicd_orchestrator_service import (
    CICDOrchestratorService,
    PipelineJob,
    PipelineStep,
    PipelineStatus,
    cicd_orchestrator_service
)


@pytest.fixture
def orchestrator():
    return CICDOrchestratorService()


def test_create_job_structure(orchestrator):
    steps_config = [
        {"name": "lint", "run": "npm run lint"},
        {"name": "test", "run": "pytest"},
        {"name": "build", "run": "npm run build"}
    ]
    job = orchestrator.create_job(
        project_id="proj_101",
        commit_sha="a1b2c3d4e5f6",
        step_commands=steps_config,
        branch="main"
    )
    assert job.project_id == "proj_101"
    assert job.commit_sha == "a1b2c3d4e5f6"
    assert job.branch == "main"
    assert len(job.steps) == 3
    assert job.steps[0].name == "lint"
    assert job.steps[0].command == "npm run lint"
    assert job.status == PipelineStatus.PENDING


def test_start_job_lifecycle(orchestrator):
    job = orchestrator.create_job("proj_1", "sha1", [{"name": "s1", "run": "echo 1"}])
    assert job.status == PipelineStatus.PENDING
    assert job.started_at is None

    started = orchestrator.start_job(job.job_id)
    assert started is not None
    assert started.status == PipelineStatus.RUNNING
    assert started.started_at is not None


def test_record_step_result_success(orchestrator):
    job = orchestrator.create_job(
        "proj_1", "sha1",
        [{"name": "s1", "run": "echo 1"}, {"name": "s2", "run": "echo 2"}]
    )
    orchestrator.start_job(job.job_id)

    orchestrator.record_step_result(job.job_id, 0, exit_code=0, duration=2.5, stdout="step 1 passed")
    assert job.steps[0].status == PipelineStatus.PASSED
    assert job.steps[0].duration_seconds == 2.5
    assert job.steps[0].stdout_log == "step 1 passed"

    orchestrator.record_step_result(job.job_id, 1, exit_code=0, duration=3.0, stdout="step 2 passed")
    assert job.steps[1].status == PipelineStatus.PASSED
    assert job.status == PipelineStatus.PASSED
    assert job.completed_at is not None


def test_record_step_result_failure(orchestrator):
    job = orchestrator.create_job(
        "proj_1", "sha1",
        [{"name": "s1", "run": "echo 1"}, {"name": "s2", "run": "echo 2"}]
    )
    orchestrator.start_job(job.job_id)

    orchestrator.record_step_result(job.job_id, 0, exit_code=0, duration=1.0)
    orchestrator.record_step_result(job.job_id, 1, exit_code=1, duration=1.2, stderr="command not found")
    assert job.steps[1].status == PipelineStatus.FAILED
    assert job.status == PipelineStatus.FAILED
    assert job.completed_at is not None


def test_invalid_job_or_step_index(orchestrator):
    res = orchestrator.record_step_result("nonexistent", 0, 0, 1.0)
    assert res is None

    job = orchestrator.create_job("proj_1", "sha1", [{"name": "s1", "run": "echo 1"}])
    res_invalid_idx = orchestrator.record_step_result(job.job_id, 99, 0, 1.0)
    assert res_invalid_idx is None
