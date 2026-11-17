# Task Manager API — End-to-End DevOps Reference Project

[![CI](https://github.com/mukesh-ma/task-manager-devops/actions/workflows/ci.yml/badge.svg)](https://github.com/mukesh-ma/task-manager-devops/actions/workflows/ci.yml)
[![CD](https://github.com/mukesh-ma/task-manager-devops/actions/workflows/cd.yml/badge.svg)](https://github.com/mukesh-ma/task-manager-devops/actions/workflows/cd.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A real, working task-management REST API (FastAPI + PostgreSQL + Redis, JWT auth)
wrapped in the full lifecycle a production service actually needs: automated
tests, security scanning, containerization, Kubernetes deployment, infrastructure
as code, and observability. This repo is meant to demonstrate DevOps practice
end-to-end, not just a "hello world" in a Dockerfile.

## Why this project

Most portfolio DevOps projects containerize a static site. This one instead ships
a stateful, authenticated API with a real database and cache, so every layer of
the pipeline has something meaningful to do: migrations matter, secrets matter,
health checks matter, and there's actual application logic for the test suite
and security scanners to exercise.

## Architecture

```
Developer → GitHub → CI (lint/test/scan) → CD (build/push image)
   → GHCR → Kubernetes (EKS) → RDS Postgres
   → Prometheus + Grafana (metrics, alerts, dashboards)
```

| Layer | Tooling | What it does |
|---|---|---|
| Application | FastAPI, SQLAlchemy, Pydantic | JWT-authenticated REST API for tasks, with `/health` and `/metrics` endpoints |
| Data | PostgreSQL, Redis | Persistent storage + caching/rate-limiting layer |
| Containerization | Docker (multi-stage), Docker Compose | Minimal non-root runtime image; full local stack in one command |
| CI | GitHub Actions | ruff lint, pytest across Python 3.11/3.12 with coverage, bandit SAST, pip-audit dependency scan, Trivy image scan |
| CD | GitHub Actions, GHCR | Builds and pushes versioned images, rolls out to staging automatically, to production on tagged release (manual approval gate) |
| Orchestration | Kubernetes | Deployment with rolling updates, readiness/liveness probes, resource limits, non-root security context, HPA, Ingress + TLS |
| Infrastructure | Terraform | AWS VPC, EKS cluster, RDS Postgres — fully codified, remote-state ready |
| Observability | Prometheus, Grafana | Request rate/latency/error-rate metrics, alert rules, starter dashboard |

## Repository layout

```
app/                  FastAPI application (auth, tasks, health, metrics)
tests/                pytest suite (auth flow, task CRUD, health, metrics)
k8s/                  Deployment, Service, Ingress, HPA, ConfigMap, Secret template
terraform/            VPC, EKS, RDS as infrastructure-as-code
monitoring/           Prometheus scrape config, alert rules, Grafana dashboard
.github/workflows/    ci.yml (test/lint/scan) and cd.yml (build/push/deploy)
docker-compose.yml    Full local stack: api + postgres + redis + prometheus + grafana
Dockerfile            Multi-stage, non-root, health-checked production image
```

## Quickstart (local)

```bash
git clone https://github.com/mukesh-ma/task-manager-devops.git
cd task-manager-devops
cp .env.example .env
make docker-up
```

- API docs: http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (`admin` / `admin`) — import the dashboard from `monitoring/grafana/dashboards/`

Try it:

```bash
curl -X POST localhost:8000/auth/register -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"supersecret"}'

TOKEN=$(curl -s -X POST localhost:8000/auth/login \
  -d "username=you@example.com&password=supersecret" | jq -r .access_token)

curl -X POST localhost:8000/tasks -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Ship the pipeline","status":"in_progress"}'
```

## Running tests locally

```bash
make install
make test   # pytest with coverage, uses an in-memory SQLite DB — no external deps
make lint   # ruff + bandit
```

## Deploying to real infrastructure

1. **Provision AWS infra**: see `terraform/README.md` — stands up a VPC, EKS
   cluster, and RDS Postgres instance.
2. **Point kubectl at the cluster**: `aws eks update-kubeconfig ...` (output by Terraform).
3. **Create the real secret** from `k8s/secret.example.yaml` (never commit the filled-in version).
4. **Apply manifests**: `kubectl apply -f k8s/`
5. **Wire up CD**: add `KUBE_CONFIG_STAGING` / `KUBE_CONFIG_PROD` as repo secrets
   so `cd.yml` can roll out new images automatically. Production deploys are
   gated behind a GitHub Environment approval — configure that under
   **Settings → Environments → production**.

## Design decisions worth calling out

- **Non-root containers everywhere** — both the Docker image and the Kubernetes
  `securityContext` run as an unprivileged user with a read-only root filesystem.
- **Secrets never touch git** — `k8s/secret.yaml` and `.env` are gitignored; the
  Terraform RDS module uses an AWS-managed master password instead of a plaintext one.
- **Staging auto-deploys, production requires a tag + manual approval** — a
  realistic promotion gate rather than "every push goes straight to prod."
- **OIDC-ready CD** — the workflow requests `id-token: write` so it can be
  switched from long-lived cloud credentials to short-lived OIDC-assumed roles.
- **/health and /metrics are first-class** — Kubernetes probes and Prometheus
  scraping both depend on these, and they're wired in from the start rather
  than bolted on later.

## License

MIT — see [LICENSE](LICENSE).
