# AI Toolkit

<p align="center">
  <img src="https://img.shields.io/github/actions/workflow/status/ankitsingh7392/ai-toolkit/ci.yml?branch=main&label=CI&logo=github" alt="CI">
  <img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit" alt="pre-commit">
  <img src="https://img.shields.io/badge/code%20style-ruff-000000?logo=python" alt="Ruff">
  <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/uv-package%20manager-blueviolet" alt="uv">
  <img src="https://img.shields.io/github/license/ankitsingh7392/ai-toolkit" alt="License">
</p>

<p align="center">
  A mono-repo of production-grade AI projects — each isolated, enterprise-ready, and built for real-world use.
</p>

---

## Table of Contents

- [Projects](#projects)
  - [FailSage](#-failsage)
- [Repo Setup](#repo-setup)
- [Repository Standards](#repository-standards)
- [Project Structure](#project-structure)
- [Contributing](#contributing)

---

## Projects

| Project | Language | Status | Description |
|---------|----------|--------|-------------|
| [failsage](projects/failsage/) | Python + TypeScript | Active | AI-Powered QE Bug Triage & Root Cause Intelligence — Jenkins Integrated |

---

### 🔬 FailSage

> **AI reads your failures, so you don't have to.**

FailSage integrates into Jenkins CI/CD pipelines, receives JUnit XML test results via webhook, analyzes failures asynchronously with Claude, clusters duplicates, detects flaky tests, and surfaces regression insights — all without blocking your pipeline.

**Full docs:** [`projects/failsage/README.md`](projects/failsage/README.md)

#### Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI + Pydantic v2 + Celery + Redis |
| AI | Anthropic Claude (claude-sonnet-4-6) |
| Database | PostgreSQL 16 + SQLAlchemy 2.0 async + Alembic |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Infra | Docker Compose / Kubernetes |

#### Quick Start — Docker

Requirements: Docker Desktop ≥ 4.x (includes Compose v2)

```bash
cd projects/failsage

# Copy config and optionally add an Anthropic key (blank = mock mode)
cp .env.example .env

# Start all 6 services (postgres, redis, backend, worker, flower, frontend)
make up

# Send a simulated Jenkins build and watch analysis complete
make test
```

| URL | What |
|-----|------|
| http://localhost:3000 | QE Dashboard |
| http://localhost:8000/docs | API docs (Swagger) |
| http://localhost:5555 | Celery Flower |

Other useful commands:

```bash
make seed          # seed 5 sample builds
make logs          # tail backend + worker
make clean         # stop + delete volumes
```

#### Quick Start — Kubernetes

Requirements: a running cluster, `kubectl` access, nginx Ingress controller, a container registry.

```bash
cd projects/failsage

# 1. Build and push images
export REGISTRY=ghcr.io/your-org
export TAG=$(git rev-parse --short HEAD)
docker build -t $REGISTRY/failsage-backend:$TAG  ./backend
docker build -t $REGISTRY/failsage-frontend:$TAG ./frontend
docker push $REGISTRY/failsage-backend:$TAG
docker push $REGISTRY/failsage-frontend:$TAG

# 2. Patch image placeholders
sed -i "s|<YOUR_REGISTRY>/failsage-backend:IMAGE_TAG|$REGISTRY/failsage-backend:$TAG|g"   k8s/backend.yaml k8s/worker.yaml
sed -i "s|<YOUR_REGISTRY>/failsage-frontend:IMAGE_TAG|$REGISTRY/failsage-frontend:$TAG|g" k8s/frontend.yaml

# 3. Create namespace + secrets
kubectl create namespace failsage
kubectl -n failsage create secret generic failsage-secrets \
  --from-literal=ANTHROPIC_API_KEY=sk-ant-... \
  --from-literal=POSTGRES_PASSWORD=$(openssl rand -base64 24)

# 4. Edit k8s/ingress.yaml — replace failsage.example.com with your hostname

# 5. Apply everything
kubectl apply -k k8s/

# 6. Watch pods come up
kubectl -n failsage get pods -w
```

Full Kubernetes guide (TLS, scaling, cert-manager, teardown): [`projects/failsage/README.md#kubernetes-deployment`](projects/failsage/README.md#kubernetes-deployment)

#### Local Development (No Docker)

```bash
cd projects/failsage

# Start only infrastructure
docker compose up -d postgres redis

# Backend (hot-reload)
cd backend
pip install uv setuptools && uv pip install --system -e ".[dev]"
export DATABASE_URL="postgresql+asyncpg://failsage:failsage@localhost:5432/failsage"
export DATABASE_URL_SYNC="postgresql+psycopg2://failsage:failsage@localhost:5432/failsage"
export CELERY_BROKER_URL="redis://localhost:6379/0"
export CELERY_RESULT_BACKEND="redis://localhost:6379/0"
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Celery worker (separate terminal)
celery -A app.core.celery_app worker --loglevel=info

# Frontend (separate terminal)
cd frontend && npm install && npm run dev   # http://localhost:5173
```

---

## Repo Setup

### Prerequisites

- [uv](https://docs.astral.sh/uv/) — Python package manager
- [pre-commit](https://pre-commit.com/) — Git hook manager
- [Go](https://go.dev/) *(for Go projects)*
- [Java 17+](https://adoptium.net/) *(for Java projects)*

### Setup

```bash
# Clone the repo
git clone https://github.com/ankitsingh7392/ai-toolkit.git
cd ai-toolkit

# Install Python toolchain
uv sync

# Install pre-commit hooks
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg
```

### Running Hooks Manually

```bash
# Run all hooks on all files
uv run pre-commit run --all-files

# Run a specific hook
uv run pre-commit run ruff --all-files
uv run pre-commit run gitleaks --all-files
```

---

## Repository Standards

- **Conventional Commits** for all commit messages and PR titles
- **Pre-commit hooks** (ruff, shellcheck, golangci-lint, gitleaks) run before every commit
- **CI checks** (MegaLinter) run on every PR — Python, Shell, Go, Java, YAML, Markdown
- **Secret scanning** via Gitleaks on every PR and push
- **Branch protection** — no direct pushes to `main`, PRs required

---

## Project Structure

```
ai-toolkit/
├── .github/
│   ├── workflows/              # CI/CD pipelines
│   ├── ISSUE_TEMPLATE/         # Bug reports & feature requests
│   └── PULL_REQUEST_TEMPLATE.md
├── projects/
│   └── failsage/               # AI QE triage platform
│       ├── backend/            # FastAPI + Celery
│       ├── frontend/           # React dashboard
│       ├── k8s/                # Kubernetes manifests
│       ├── tests/              # Sample data + simulators
│       ├── docker-compose.yml
│       ├── Makefile
│       └── README.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
└── pyproject.toml
```

---

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a PR. All contributions must pass pre-commit hooks and CI checks.

## Security

To report a vulnerability, see [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE)
