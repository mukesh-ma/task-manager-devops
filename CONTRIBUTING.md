# Contributing

## Local setup

```bash
git clone https://github.com/<you>/task-manager-devops.git
cd task-manager-devops
make install
cp .env.example .env
make docker-up   # starts api + postgres + redis + prometheus + grafana
```

## Workflow

1. Branch from `develop`: `git checkout -b feat/short-description`
2. Write code + tests. Aim to keep coverage from dropping (`make test`).
3. Run `make lint` before pushing — CI will fail the same checks otherwise.
4. Open a PR into `develop`. CI (lint, tests on 3.11/3.12, security scan, Docker
   build + Trivy scan) must pass before merge.
5. `develop` -> `main` merges trigger a build + push to GHCR and a staging
   deploy. Tagging a release (`git tag v1.2.0 && git push --tags`) promotes
   that image to production after manual approval in the `production`
   GitHub Environment.

## Commit style

Conventional Commits are appreciated but not enforced:
`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`.
