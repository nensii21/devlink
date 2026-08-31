# CI/CD Orchestrator Service

The DevLink CI/CD Orchestrator provides a robust backend pipeline execution engine capable of parallelizing tasks and deploying binaries safely to production environments.

## Core Architecture

### 1. Directed Acyclic Graph (DAG) Execution
Pipelines are organized strictly into `PipelineStage`s which contain `PipelineJob`s. Each Job can specify a list of dependencies (`depends_on: ["job_id"]`). 
The core engine (`resolve_next_jobs`) analyzes this definition dynamically, calculating a DAG. This allows jobs with no remaining dependencies to run in parallel, while blocking downstream jobs until prerequisites pass.

### 2. Failure Propagation
If a job fails (`exit_code != 0`), the DAG evaluator automatically recursively marks all jobs that depend on it as `SKIPPED`. If any job in the pipeline fails, the entire pipeline is marked as `FAILED` upon completion of the remaining active jobs.

### 3. Artifact Metadata Management
When build jobs complete, they can publish Artifacts (e.g. Docker images, tarballs). The orchestrator tracks these artifacts (`publish_artifact`) entirely through metadata, assuming the actual bits are stored in external registries like AWS S3, ECR, or Nexus.

### 4. Deployment Strategies
The orchestration layer contains pluggable `DeploymentStrategy` handlers for moving an artifact between environments (`promote_artifact`):
- `RollingDeployment`: Deploys linearly across all nodes.
- `CanaryDeployment`: Dynamically sweeps traffic splits (e.g. 10% -> 50% -> 100%) checking health metrics between thresholds.
- `BlueGreenDeployment`: Spools up inactive infrastructure, executes smoke tests, and executes a full router traffic swap instantly.

## Webhook Integrations
The orchestrator natively exposes `handle_webhook_trigger`, mapping incoming payloads from `GitHub Actions` and `GitLab CI` into generic internal DAG pipeline definitions.

## Usage
```python
from app.services.cicd_orchestrator_service import cicd_orchestrator_service, CanaryDeployment

# 1. Resolve DAG jobs ready to execute
ready_jobs = cicd_orchestrator_service.resolve_next_jobs("pipe_123")

# 2. Complete a job
cicd_orchestrator_service.record_job_result("pipe_123", "build_ui", 0)

# 3. Promote Artifact Canary
canary = CanaryDeployment(traffic_percentages=[10, 50, 100])
cicd_orchestrator_service.promote_artifact("art_backend_1.0.0", "production", canary)
```
