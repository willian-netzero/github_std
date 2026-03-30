# NetZero GitHub Standards

This repository defines the **development standards, documentation templates, and AI-assisted automation agents** used across NetZero's engineering projects. Its purpose is to establish a consistent, scalable baseline that any team or project can adopt from day one.

---

## Repository Structure

```
github_std/
├── docs-templates/          # Markdown templates for project documentation
│   ├── architecture.md      # System architecture & ADR template
│   ├── development-guide.md # Coding conventions, branching, and workflow rules
│   ├── roadmap.md           # Sprint planning and backlog template
│   ├── backlog.md           # Product backlog and issue tracking template
│   └── security.md          # Security policies and secret management rules
│
├── agents/                  # AI agents that automate GitHub workflows
│   ├── webhook-handler/     # Entry point: receives GitHub webhook events
│   ├── code-reviewer/       # Reviews pull requests and suggests improvements
│   ├── pr-summarizer/       # Generates PR summaries for team review
│   ├── security-scanner/    # Scans code for secrets and security issues
│   ├── test-runner/         # Runs tests and reports results on PRs
│   ├── architecture-guard/  # Validates architecture and stack conventions
│   └── shared/              # Shared utilities (GitHub client, stack detector)
│
├── agents-architecture.html # Visual overview of the agents system
├── dev-best-practices.html  # Best practices guide (HTML export)
├── dev-implementation-guide.html # Implementation guide (HTML export)
└── documentation-v0.6.html # Full documentation strategy for NetZero
```

---

## Documentation Templates (`docs-templates/`)

Copy these templates into your project's `docs/` folder at project creation. Each template is self-documented with inline instructions.

| Template | Purpose |
|---|---|
| `architecture.md` | Describe system components, stack, layer rules, data model, integrations, and ADRs |
| `development-guide.md` | Define how the team writes code: conventions, branch strategy, PR rules, testing |
| `roadmap.md` | Track what's in progress, upcoming, and out of scope |
| `backlog.md` | Manage features and bugs in a lightweight markdown-native format |
| `security.md` | Document security rules, secret management, auth patterns, and incident procedures |

### Usage

```bash
# Copy all templates into a new project
cp -r github_std/docs-templates/ my-project/docs/
```

Fill in the placeholders (`_e.g. ..._, YYYY-MM-DD, @developer`) with your project's real values.

---

## AI Agents (`agents/`)

These agents automate common GitHub workflows via webhooks. They are triggered by GitHub events (PRs opened, commits pushed, etc.) and run as lightweight services.

### Agents Overview

| Agent | Trigger | What it does |
|---|---|---|
| `webhook-handler` | All GitHub events | Routes events to the appropriate agent |
| `code-reviewer` | PR opened / updated | Reviews code quality and leaves inline comments |
| `pr-summarizer` | PR opened / updated | Generates a human-readable summary of changes |
| `security-scanner` | Push / PR | Detects hardcoded secrets and known vulnerability patterns |
| `test-runner` | Push / PR | Executes the test suite and reports pass/fail status |
| `architecture-guard` | PR opened | Validates that changes respect the defined layer boundaries |

### Running Locally

```bash
cd agents/webhook-handler
pip install -r requirements.txt
python app.py
```

Configure your GitHub repository to send webhook events to the running handler's endpoint.

---

## Best Practices

The HTML files at the root provide the rationale behind these standards:

- **`documentation-v0.6.html`** — NetZero's documentation strategy and methodology
- **`dev-best-practices.html`** — Coding and process best practices
- **`dev-implementation-guide.html`** — Step-by-step implementation guidance
- **`agents-architecture.html`** — Architecture diagram for the agents system

---

## Contributing

1. Branch off `main` using the convention: `feat/`, `fix/`, `docs/`, `refactor/`
2. Follow the [Development Guide](docs-templates/development-guide.md) conventions
3. Open a PR with a clear description — the `pr-summarizer` agent will help
4. At least one review required before merge

---

## Maintainers

NetZero Engineering Team — [willian.menezes@netzero.green](mailto:willian.menezes@netzero.green)
