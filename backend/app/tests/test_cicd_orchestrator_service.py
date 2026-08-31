import pytest
from app.services.cicd_orchestrator_service import (
    CICDOrchestratorService,
    PipelineStatus,
    BlueGreenDeployment,
    CanaryDeployment
)


@pytest.fixture
def cicd():
    return CICDOrchestratorService()


def test_dag_resolution_and_execution(cicd):
    stages = [
        {
            "name": "Build",
            "jobs": [
                {"id": "build_ui", "run": "npm run build"},
                {"id": "build_api", "run": "make build"}
            ]
        },
        {
            "name": "Test",
            "jobs": [
                {"id": "test_ui", "run": "npm run test", "depends_on": ["build_ui"]},
                {"id": "test_api", "run": "make test", "depends_on": ["build_api"]},
                {"id": "integration", "run": "make e2e", "depends_on": ["build_ui", "build_api"]}
            ]
        }
    ]
    
    pipeline = cicd.create_pipeline("proj1", "abcd123", "main", stages)
    
    # Initially, only jobs with no dependencies are eligible
    eligible = cicd.resolve_next_jobs(pipeline.pipeline_id)
    assert len(eligible) == 2
    assert set([j.job_id for j in eligible]) == {"build_ui", "build_api"}
    
    # Finish build_ui successfully
    cicd.record_job_result(pipeline.pipeline_id, "build_ui", 0)
    
    # Now test_ui should be eligible, but integration is still waiting on build_api
    eligible = cicd.resolve_next_jobs(pipeline.pipeline_id)
    assert len(eligible) == 2  # build_api (still pending) and test_ui
    assert set([j.job_id for j in eligible]) == {"build_api", "test_ui"}
    
    # Finish build_api successfully
    cicd.record_job_result(pipeline.pipeline_id, "build_api", 0)
    
    # Now integration and test_api are eligible
    eligible = cicd.resolve_next_jobs(pipeline.pipeline_id)
    assert set([j.job_id for j in eligible]) == {"test_ui", "test_api", "integration"}


def test_failure_propagation(cicd):
    stages = [
        {"name": "Build", "jobs": [{"id": "build_core", "run": "make"}]},
        {"name": "Test", "jobs": [{"id": "test_core", "depends_on": ["build_core"]}]},
        {"name": "Deploy", "jobs": [{"id": "deploy_prod", "depends_on": ["test_core"]}]}
    ]
    pipeline = cicd.create_pipeline("proj2", "efg456", "main", stages)
    
    # Fail the build
    cicd.record_job_result(pipeline.pipeline_id, "build_core", 1)
    
    assert pipeline.status == PipelineStatus.FAILED
    
    # Dependent jobs should be skipped recursively
    job_map = {j.job_id: j for stage in pipeline.stages for j in stage.jobs}
    assert job_map["test_core"].status == PipelineStatus.SKIPPED
    assert job_map["deploy_prod"].status == PipelineStatus.SKIPPED


def test_artifact_management_and_deployment(cicd):
    art = cicd.publish_artifact("backend-image", "1.0.0", "s3://bucket/img.tar")
    assert art.environment == "build"
    
    bg = BlueGreenDeployment()
    success = cicd.promote_artifact(art.artifact_id, "production", bg)
    assert success is True
    assert art.environment == "production"
    
    canary = CanaryDeployment(traffic_percentages=[50, 100])
    success = cicd.promote_artifact(art.artifact_id, "canary", canary)
    assert success is True
    assert art.environment == "canary"


def test_webhook_integration(cicd):
    # Github payload mock
    gh_payload = {
        "ref": "refs/heads/feature-1",
        "after": "deadbeef",
        "repository": {"name": "repo_github"}
    }
    pipe_gh = cicd.handle_webhook_trigger("github", gh_payload)
    assert pipe_gh.project_id == "repo_github"
    assert pipe_gh.commit_sha == "deadbeef"
    assert pipe_gh.branch == "feature-1"
    
    # Gitlab payload mock
    gl_payload = {
        "ref": "refs/heads/master",
        "checkout_sha": "c0ffee",
        "project": {"path_with_namespace": "org/repo_gitlab"}
    }
    pipe_gl = cicd.handle_webhook_trigger("gitlab", gl_payload)
    assert pipe_gl.project_id == "org/repo_gitlab"
    assert pipe_gl.commit_sha == "c0ffee"
    assert pipe_gl.branch == "master"
