# FailSage

> **AI reads your failures, so you don't have to.**

FailSage is an AI-powered QE bug triage and root cause intelligence platform that integrates directly into Jenkins CI/CD pipelines. It receives JUnit XML test results via webhook, analyzes failures asynchronously using Claude, clusters duplicates, detects flaky tests, and surfaces regression insights — all without blocking your pipeline.

<table>
<tr>
<td width="50%">
<img src="docs/assets/dashboard-dark.png" alt="FailSage dashboard — dark mode" />
<p align="center"><em>Dashboard — dark mode</em></p>
</td>
<td width="50%">
<img src="docs/assets/dashboard-light.png" alt="FailSage dashboard — light mode" />
<p align="center"><em>Dashboard — light mode</em></p>
</td>
</tr>
<tr>
<td colspan="2">
<img src="docs/assets/run-detail-dark.png" alt="FailSage run detail with AI analysis" />
<p align="center"><em>Run detail — AI build assessment, severity-tagged failures, and root cause analysis</em></p>
</td>
</tr>
</table>

---

## Table of Contents

- [Architecture](#architecture)
- [Quick Start — Docker (Recommended)](#quick-start--docker-recommended)
- [Local Development (No Docker)](#local-development-no-docker)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Jenkins Integration](#jenkins-integration)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [AI Analysis Design](#ai-analysis-design)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)

---

## Architecture

```
Jenkins
  │
  └─► POST /ci/jenkins/test-results      ← FastAPI  (returns run_id in <50ms)
                    │
              Redis Queue
                    │
         Celery Worker (async)
         ├── JUnit XML Parser
         ├── Failure Clusterer            (TF-IDF + cosine similarity)
         ├── AI Analysis                  (Claude per cluster — not per test)
         ├── Flaky Detector               (pattern matching + historical rates)
         ├── Build Regression Insight     (commit-level reasoning)
         └── Slack / Jira notifications
                    │
             PostgreSQL 16
                    │
         React Dashboard                  (dark/light, real-time polling, filters)
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| FastAPI backend | 8000 | Webhook ingestion + REST API |
| Celery worker | — | Async AI analysis pipeline |
| PostgreSQL 16 | 5432 | Persistent storage |
| Redis 7 | 6379 | Celery broker + result backend |
| React frontend | 3000 | QE engineer dashboard |
| Flower | 5555 | Celery task monitor |

---

## Quick Start — Docker (Recommended)

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) ≥ 4.x  (includes Compose v2)
- An [Anthropic API key](https://console.anthropic.com/) — *optional; mock mode works without one*

### 1. Clone and configure

```bash
git clone <repo-url>
cd ai-toolkit/projects/failsage

cp .env.example .env
```

Open `.env` and set your Anthropic key (or leave it blank for mock responses):

```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### 2. Start all services

```bash
make up
```

This builds all Docker images and starts postgres, redis, backend, worker, flower, and frontend. On first run it also applies Alembic migrations automatically.

Wait ~15 seconds for the backend to finish migrating, then open:

| URL | What you'll find |
|-----|------------------|
| http://localhost:3000 | QE Dashboard |
| http://localhost:8000/docs | Interactive API docs (Swagger) |
| http://localhost:5555 | Celery Flower (task monitor) |

### 3. Send a test Jenkins payload

```bash
make test
```

This runs `tests/simulate_jenkins.py` which POSTs a realistic JUnit XML payload and polls until analysis completes.

To simulate multiple builds:

```bash
make seed          # sends 5 builds
cd tests && python simulate_jenkins.py --runs=10 --poll
```

### 4. Useful Makefile targets

```bash
make up            # Build + start all services (idempotent)
make down          # Stop containers (keep volumes)
make clean         # Stop containers + delete volumes + clear pycache
make build         # Force rebuild all images (no cache)
make logs          # Tail backend + worker logs
make test          # Send one Jenkins payload and poll
make seed          # Send 5 Jenkins payloads
```

---

## Local Development (No Docker)

Useful for faster iteration on the backend or frontend.

### Requirements

- Python 3.11+
- Node.js 20+
- PostgreSQL 16 running locally (or use the Docker Compose postgres only)
- Redis running locally (or use the Docker Compose redis only)

### Start only the infrastructure

```bash
docker compose up -d postgres redis
```

### Backend

```bash
cd backend

# Install dependencies
pip install uv setuptools
uv pip install --system -e ".[dev]"

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://failsage:failsage@localhost:5432/failsage"
export DATABASE_URL_SYNC="postgresql+psycopg2://failsage:failsage@localhost:5432/failsage"
export CELERY_BROKER_URL="redis://localhost:6379/0"
export CELERY_RESULT_BACKEND="redis://localhost:6379/0"
export ANTHROPIC_API_KEY="sk-ant-..."   # or leave blank for mock mode

# Apply migrations
alembic upgrade head

# Start the API server (hot-reload)
uvicorn app.main:app --reload --port 8000
```

### Celery worker (separate terminal)

```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info --concurrency=4
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # Vite dev server with HMR at http://localhost:5173
```

The Vite dev server proxies `/api/` to `http://localhost:8000` automatically (configured in `vite.config.ts`).

### Run unit tests

```bash
# Parser tests (no DB or AI required)
pip install defusedxml
python tests/test_parser.py
```

---

## Kubernetes Deployment

All manifests live in `k8s/`. They are plain YAML — no Helm required, though Kustomize is supported.

### Prerequisites

- A running Kubernetes cluster (EKS, GKE, AKS, k3s, minikube, etc.)
- `kubectl` configured with cluster access
- An nginx Ingress controller (see step 1)
- Docker images built and pushed to a registry accessible by the cluster

### Step 1 — Install nginx Ingress controller

Skip if your cluster already has one.

```bash
helm upgrade --install ingress-nginx ingress-nginx \
  --repo https://kubernetes.github.io/ingress-nginx \
  --namespace ingress-nginx --create-namespace \
  --set controller.replicaCount=2
```

### Step 2 — Build and push images

```bash
export REGISTRY=ghcr.io/your-org   # or Docker Hub, ECR, GCR, etc.
export TAG=$(git rev-parse --short HEAD)

docker build -t $REGISTRY/failsage-backend:$TAG  ./backend
docker build -t $REGISTRY/failsage-frontend:$TAG ./frontend

docker push $REGISTRY/failsage-backend:$TAG
docker push $REGISTRY/failsage-frontend:$TAG
```

Then replace the image placeholders in the manifests:

```bash
# macOS / Linux
sed -i "s|<YOUR_REGISTRY>/failsage-backend:IMAGE_TAG|$REGISTRY/failsage-backend:$TAG|g" k8s/backend.yaml k8s/worker.yaml
sed -i "s|<YOUR_REGISTRY>/failsage-frontend:IMAGE_TAG|$REGISTRY/failsage-frontend:$TAG|g" k8s/frontend.yaml
```

### Step 3 — Configure secrets

Edit `k8s/secret.yaml` with your real values, **or** (preferred) create the secret directly and skip committing credentials:

```bash
kubectl create namespace failsage

kubectl -n failsage create secret generic failsage-secrets \
  --from-literal=ANTHROPIC_API_KEY=sk-ant-api03-... \
  --from-literal=POSTGRES_PASSWORD=$(openssl rand -base64 24) \
  --from-literal=SLACK_WEBHOOK_URL=https://hooks.slack.com/... \
  --from-literal=JIRA_URL=https://yourorg.atlassian.net \
  --from-literal=JIRA_TOKEN=your-token
```

If you create the secret manually, remove `secret.yaml` from `k8s/kustomization.yaml` before applying.

### Step 4 — Set your hostname

Edit `k8s/ingress.yaml` and replace `failsage.example.com` with your real domain.

### Step 5 — Apply everything

```bash
# Apply all manifests at once with Kustomize
kubectl apply -k k8s/

# Or apply individually in dependency order
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/worker.yaml
kubectl apply -f k8s/frontend.yaml
kubectl apply -f k8s/ingress.yaml
```

### Step 6 — Verify

```bash
# Watch all pods come up
kubectl -n failsage get pods -w

# Once backend pod is Running, confirm migrations ran
kubectl -n failsage logs -l app=backend -c migrate

# Check ingress
kubectl -n failsage get ingress
```

Expected pod states:

```
NAME                        READY   STATUS    RESTARTS
postgres-0                  1/1     Running   0
redis-xxxx                  1/1     Running   0
backend-xxxx                1/1     Running   0
backend-yyyy                1/1     Running   0
worker-xxxx                 1/1     Running   0
worker-yyyy                 1/1     Running   0
frontend-xxxx               1/1     Running   0
frontend-yyyy               1/1     Running   0
flower-xxxx                 1/1     Running   0
```

### Step 7 — Access the dashboard

Point your domain at the Ingress controller's external IP:

```bash
# Get the Ingress external IP
kubectl -n ingress-nginx get svc ingress-nginx-controller

# Update your DNS A record, or for quick testing add to /etc/hosts:
echo "<EXTERNAL-IP> failsage.example.com" | sudo tee -a /etc/hosts
```

Then open http://failsage.example.com.

### Scaling workers

```bash
# Scale Celery workers to handle more concurrent builds
kubectl -n failsage scale deployment worker --replicas=4
```

### TLS with cert-manager

```bash
# Install cert-manager
helm upgrade --install cert-manager cert-manager \
  --repo https://charts.jetstack.io \
  --namespace cert-manager --create-namespace \
  --set installCRDs=true

# Create a ClusterIssuer (edit email)
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: you@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: nginx
EOF
```

Then uncomment the `tls` and `cert-manager.io/cluster-issuer` sections in `k8s/ingress.yaml` and re-apply.

### Tear down

```bash
kubectl delete namespace failsage
```

This removes all FailSage resources. The PVC is deleted with the namespace; your postgres data will be lost. Snapshot the PVC first if you need to preserve data.

---

## Jenkins Integration

Add this stage to your `Jenkinsfile` immediately after the test stage:

```groovy
stage('FailSage Analysis') {
    steps {
        script {
            def xml = readFile('test-results/junit.xml')
            def payload = groovy.json.JsonOutput.toJson([
                ci: [
                    build_id   : env.BUILD_NUMBER,
                    job_name   : env.JOB_NAME,
                    git_commit : env.GIT_COMMIT,
                    branch     : env.BRANCH_NAME,
                    environment: 'staging',
                    jenkins_url: env.BUILD_URL
                ],
                junit_xml: xml
            ])
            def resp = httpRequest(
                url         : 'http://failsage:8000/ci/jenkins/test-results',
                httpMode    : 'POST',
                contentType : 'APPLICATION_JSON',
                requestBody : payload
            )
            def result = readJSON text: resp.content
            echo "FailSage run_id: ${result.run_id}"
            env.FAILSAGE_RUN_ID = result.run_id
        }
    }
}
```

Replace `http://failsage:8000` with your actual backend URL (Docker service name, k8s Service DNS, or external hostname).

**Jenkins responds in < 50 ms** — FailSage is non-blocking.

---

## API Reference

### `POST /ci/jenkins/test-results`

Receive a Jenkins build. Returns a `run_id` immediately; analysis runs async.

```jsonc
// Request
{
  "ci": {
    "build_id": "1042",
    "job_name": "backend-regression",
    "git_commit": "a3f8c21d9e04b15f",
    "branch": "main",
    "environment": "staging",
    "jenkins_url": "https://jenkins.example.com/job/backend-regression/1042/"
  },
  "junit_xml": "<testsuites>...</testsuites>"
}

// Response — 202 Accepted
{
  "run_id": "f3a9c12d8b7e4501",
  "status": "pending",
  "message": "Analysis queued.",
  "polling_url": "/runs/f3a9c12d8b7e4501"
}
```

### `GET /runs`

List test runs with filters.

| Query param | Type | Description |
|-------------|------|-------------|
| `job_name` | string | Filter by Jenkins job name |
| `branch` | string | Filter by git branch |
| `environment` | string | Filter by environment (staging, prod…) |
| `status` | string | `pending` \| `processing` \| `completed` \| `failed` |
| `build_at_risk` | bool | `true` = only at-risk builds |
| `date_from` | ISO 8601 | Earliest `created_at` (e.g. `2026-06-01T00:00:00`) |
| `date_to` | ISO 8601 | Latest `created_at` |
| `limit` | int (1–1000) | Max results (default 50) |

### `GET /runs/meta`

Returns distinct job names, branches, and environments — used to populate dashboard filter dropdowns.

```jsonc
{ "jobs": ["backend-regression", "ui-smoke"], "branches": ["main", "develop"], "environments": ["staging"] }
```

### `GET /runs/{run_id}`

Poll for status and build-level insight.

### `GET /failures/{run_id}`

All failures with AI analysis, severity, and cluster info.  
Optional filters: `?severity=P0`, `?category=API`, `?flaky_only=true`

### `GET /flaky-tests`

All flaky tests tracked across builds.

### `POST /feedback`

Submit QE corrections to improve AI accuracy over time.

```jsonc
{
  "test_case_id": "uuid",
  "is_helpful": false,
  "correct_category": "Infrastructure",
  "correct_severity": "P2",
  "feedback_notes": "Known infra issue, not an API bug"
}
```

---

## Configuration

All config is via environment variables (`.env` for Docker, ConfigMap + Secret for k8s).

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | *(empty)* | Claude API key — leave blank for mock mode |
| `AI_MODEL` | `claude-sonnet-4-6` | Claude model |
| `AI_MOCK_MODE` | `false` | Force mock responses (overrides API key) |
| `DATABASE_URL` | `postgresql+asyncpg://...` | Async DB URL (FastAPI) |
| `DATABASE_URL_SYNC` | `postgresql+psycopg2://...` | Sync DB URL (Celery) |
| `CELERY_BROKER_URL` | `redis://redis:6379/0` | Celery broker |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/0` | Celery result store |
| `CLUSTER_SIMILARITY_THRESHOLD` | `0.72` | Cosine similarity for failure grouping |
| `FLAKY_LOOKBACK_RUNS` | `10` | History window for flaky detection |
| `FLAKY_FAIL_RATE_THRESHOLD` | `0.3` | Fail rate below which a test is flagged flaky |
| `SLACK_WEBHOOK_URL` | *(empty)* | Enable Slack notifications |
| `JIRA_URL` | *(empty)* | Enable Jira auto-ticket creation |
| `JIRA_TOKEN` | *(empty)* | Jira Bearer token |
| `JIRA_PROJECT` | `QE` | Jira project key |
| `DEBUG` | `false` | Verbose logging |

---

## AI Analysis Design

Claude is called **once per failure cluster**, not per test.  
100 tests with the same `NullPointerException` = **1 API call**.

Each response is **strict JSON only** — FailSage rejects any response that isn't valid JSON, and the prompt explicitly forbids inventing context not present in the failure data.

### Failure categories

| Category | Examples |
|----------|---------|
| `UI` | Selenium element not found, timeout, screenshot diff |
| `API` | HTTP 4xx/5xx, connection refused, JSON parse error |
| `Database` | SQL error, connection refused, constraint violation |
| `Performance` | Duration threshold exceeded, slow query |
| `Infrastructure` | Docker/K8s error, OOM, external service down |
| `TestIssue` | Fixture failure, bad test data, known flaky pattern |

### Severity scale

| Severity | Meaning |
|----------|---------|
| P0 | Blocker — auth down, data corruption, system unavailable |
| P1 | Critical — major feature broken, no workaround |
| P2 | Major — significant degradation, workaround exists |
| P3 | Minor — cosmetic or edge case |

---

## Project Structure

```
failsage/
├── docker-compose.yml
├── Makefile
├── .env.example
├── k8s/                           # Kubernetes manifests
│   ├── kustomization.yaml         # kubectl apply -k k8s/
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── postgres.yaml              # StatefulSet + PVC + Service
│   ├── redis.yaml
│   ├── backend.yaml               # Deployment (2 replicas) + Service
│   ├── worker.yaml                # Celery worker + Flower
│   ├── frontend.yaml              # nginx + Service
│   └── ingress.yaml               # nginx Ingress
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic/                   # Database migrations
│   └── app/
│       ├── main.py                # FastAPI entry point
│       ├── core/                  # Config, DB, Celery setup
│       ├── models/
│       │   ├── db/                # SQLAlchemy ORM models
│       │   └── schemas/           # Pydantic request/response schemas
│       ├── api/routes/            # REST endpoints
│       ├── services/
│       │   ├── junit_parser.py    # JUnit XML → structured data
│       │   ├── ai_service.py      # Claude integration + prompts
│       │   ├── clustering.py      # TF-IDF failure clustering
│       │   ├── flaky_detector.py  # Flaky test detection
│       │   └── notification.py    # Slack + Jira
│       └── tasks/
│           └── analysis.py        # Main Celery pipeline
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── src/
│       ├── pages/                 # Dashboard, RunDetail
│       ├── components/            # AIPanel, FailureList, filters, etc.
│       ├── hooks/                 # useTheme
│       └── api/client.ts          # Typed API client
└── tests/
    ├── sample_junit.xml           # 15-test realistic multi-suite data
    ├── simulate_jenkins.py        # End-to-end Jenkins simulator
    └── test_parser.py             # Unit tests for XML parser
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI + Pydantic v2 |
| Async task queue | Celery + Redis |
| AI | Anthropic Claude (claude-sonnet-4-6) |
| Database | PostgreSQL 16 + SQLAlchemy 2.0 async |
| Migrations | Alembic |
| Frontend | React 18 + TypeScript + Vite |
| Styling | Tailwind CSS (class-based dark mode) |
| Charts | Recharts |
| Failure clustering | scikit-learn (TF-IDF + cosine similarity) |
| XML parsing | defusedxml (safe against XXE) |
| Notifications | Slack webhooks + Jira REST API |
| Container runtime | Docker + Compose v2 |
| Orchestration | Kubernetes + nginx Ingress |

---

## License

MIT — see [LICENSE](../../LICENSE)
