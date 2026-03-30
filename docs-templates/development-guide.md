# Development Guide

> This document is the single source of truth for how we build software in this project.
> Every contributor — internal or external — should read this before writing code.

---

## Active Scope

<!-- What this project does right now. Keep it to 2-3 sentences. -->

This project currently covers:

- [ ] _Describe the main feature or domain this repo handles_
- [ ] _Second feature if applicable_

**Out of scope (for now):** _list things people might assume are included but aren't._

---

## Architecture

<!-- High-level view. Describe layers, main components, how they connect. -->

### Stack

| Layer          | Technology            |
|----------------|-----------------------|
| Backend        | _e.g. Python/FastAPI_ |
| Frontend       | _e.g. React/TS_       |
| Database       | _e.g. PostgreSQL_     |
| Infrastructure | _e.g. Docker, K8s_    |

### Layer Structure

```
src/
├── api/          # or endpoints/ — HTTP layer (Presentation)
├── services/     # Business logic (Application)
├── models/       # Domain entities (Domain)
├── repositories/ # or dao/ — Data access (Infrastructure)
├── shared/       # Cross-cutting utilities
└── config/       # Settings, env vars
```

### Layer Rules

1. **Presentation** receives the request, calls a service, returns the response. No business logic.
2. **Application** orchestrates use cases. Calls validation, mapping, repositories.
3. **Domain** contains entities and business rules. Never imports from infrastructure.
4. **Infrastructure** handles DB, external APIs, file system. Never imported by domain.

Dependencies always flow inward: Presentation → Application → Domain ← Infrastructure.

---

## Conventions

### Naming

| Element       | Convention                           | Example                          |
|---------------|--------------------------------------|----------------------------------|
| Branches      | `feat/`, `fix/`, `refactor/`, etc.   | `feat/user-auth`                 |
| Commits       | Conventional Commits                 | `feat(auth): add JWT refresh`    |
| Files         | kebab-case                           | `user-service.py`                |
| Functions     | snake_case (Python) / camelCase (JS) | `create_user` / `createUser`     |
| Constants     | UPPER_SNAKE_CASE                     | `MAX_RETRY_COUNT`                |

### Code Style

- Linter runs on every PR and blocks merge on failure
- Formatting is enforced by `.editorconfig` + stack-specific tools (Ruff, ESLint, etc.)
- No `console.log` / `print()` in production code
- No hardcoded secrets — use environment variables

---

## Security Rules

- **Never commit secrets.** API keys, tokens, passwords go in environment variables only.
- **Never trust user input.** Validate everything at the boundary (API layer or validation layer).
- **Use parameterized queries.** No string interpolation in SQL.
- **Dependencies must be audited.** CI runs `pip audit` / `npm audit` on every PR.
- **Sensitive data must not appear in logs.** Mask PII, tokens, and credentials.
- **Docker images must not run as root** unless explicitly justified and documented.

---

## Branching & PR Flow

We use **GitHub Flow** — one long-lived branch (`main`) and short-lived feature branches.

### Workflow

```
1. Pull latest main
2. Create branch: feat/my-feature
3. Code + commit (Conventional Commits)
4. Push and open PR
5. CI runs (lint, test, architecture check)
6. Reviewer approves
7. Squash merge to main
```

### Branch Protection (main)

- Require PR before merging (no direct push)
- Require at least 1 approval
- Require CI status checks to pass
- Require branch up-to-date with main
- Require linear history (squash merge)

### PR Checklist

Every PR must fill the template. At minimum:

- [ ] Code follows layer separation guidelines
- [ ] No business logic in controllers/endpoints
- [ ] No hardcoded secrets
- [ ] Tests added or updated
- [ ] Linter passes with no warnings
- [ ] Self-reviewed my own code

---

## Definition of Done

A feature is "done" when:

- [ ] Code merged to `main` via approved PR
- [ ] All CI checks green (lint + tests + architecture)
- [ ] Test coverage meets minimum threshold
- [ ] No unresolved review comments
- [ ] README updated if behavior changed
- [ ] No tech debt introduced without a follow-up issue

---

## Local Development

### Prerequisites

<!-- List what devs need installed -->

- _e.g. Docker, Python 3.12+, Node 20+_
- _e.g. Access to `.env` template (never commit actual `.env`)_

### Getting Started

```bash
# Clone the repo
git clone git@github.com:netzero-hq/<repo-name>.git
cd <repo-name>

# Copy env template
cp .env.example .env

# Start services
docker compose up -d

# Run tests
# Python: pytest tests/
# JS/TS: npm test
```

### Environment Variables

| Variable      | Purpose                | Default    | Required |
|---------------|------------------------|------------|----------|
| `DATABASE_URL`| Database connection    | —          | Yes      |
| `API_KEY`     | External service key   | —          | Yes      |
| `LOG_LEVEL`   | Logging verbosity      | `info`     | No       |

---

## Related Documents

- [Roadmap](roadmap.md) — what's planned, in progress, and done
- [Backlog](backlog.md) — prioritized task list
- [NetZero Dev Best Practices](../dev-best-practices.html) — org-wide standards
