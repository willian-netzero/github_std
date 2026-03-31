# Architecture

> Technical architecture overview for this project. Describes the system components,
> how they communicate, and the key design decisions.

**Last updated:** _YYYY-MM-DD_

---

## System Overview

<!-- High-level diagram of the system. Use ASCII or link to a Mermaid/diagram file. -->

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client     │────▶│   API       │────▶│  Database   │
│  (Browser)   │     │  (Backend)  │     │             │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  External   │
                    │  Services   │
                    └─────────────┘
```

---

## Stack

| Component      | Technology        | Version | Notes                    |
|----------------|-------------------|---------|--------------------------|
| Backend        | _e.g. FastAPI_    | _0.110_ |                          |
| Frontend       | _e.g. React_      | _18.3_  | _TypeScript_             |
| Database       | _e.g. PostgreSQL_ | _16_    |                          |
| Cache          | _e.g. Redis_      | _7_     | _Optional_               |
| Message Queue  | _e.g. RabbitMQ_   |         | _If applicable_          |
| Container      | Docker            |         |                          |
| CI/CD          | GitHub Actions    |         |                          |

---

## Project Structure

```
project/
├── src/
│   ├── api/            # HTTP layer (routes, controllers, middleware)
│   ├── services/       # Business logic and use case orchestration
│   ├── models/         # Domain entities, schemas, types
│   ├── repositories/   # Data access (DB queries, external API clients)
│   ├── shared/         # Cross-cutting utilities
│   └── config/         # Settings, environment, constants
├── tests/
│   ├── unit/
│   └── integration/
├── docs/               # This folder
├── Dockerfile
└── README.md
```

---

## Layer Separation

### Rules

| Layer          | Responsibility                        | Can import from        | Cannot import from     |
|----------------|---------------------------------------|------------------------|------------------------|
| Presentation   | HTTP in/out, request parsing          | Application, Shared    | Domain, Infrastructure |
| Application    | Use case orchestration, business flow | Domain, Infrastructure | Presentation           |
| Domain         | Core entities and business rules      | Nothing (self-contained)| Any other layer       |
| Infrastructure | DB, external APIs, file system        | Domain, Shared         | Presentation, Application |

### Dependency Direction

```
Presentation → Application → Domain ← Infrastructure
     │                                      │
     └──────── both use Shared ─────────────┘
```

---

## Data Model

<!-- List the main entities and their relationships. -->

| Entity         | Description                           | Key fields            |
|----------------|---------------------------------------|-----------------------|
| _e.g. User_    | _System user with authentication_     | _id, email, role_     |
| _e.g. Order_   | _Purchase order submitted by user_    | _id, user_id, status_ |

---

## External Integrations

<!-- APIs, services, or systems this project communicates with. -->

| Service          | Purpose                  | Auth method     | Docs link            |
|------------------|--------------------------|-----------------|----------------------|
| _e.g. Stripe_    | _Payment processing_     | _API key_       | _https://..._        |
| _e.g. SendGrid_  | _Email delivery_         | _API key_       | _https://..._        |

---

## Key Design Decisions

<!-- Record important architectural choices and why they were made. -->
<!-- This helps future developers understand the "why" behind the system. -->

### ADR-001 — _Decision title_

- **Date:** _YYYY-MM-DD_
- **Context:** _What situation required a decision?_
- **Decision:** _What was decided?_
- **Reason:** _Why this option over alternatives?_
- **Consequences:** _What trade-offs come with this decision?_

### ADR-002 — _Decision title_

- **Date:** _YYYY-MM-DD_
- **Context:** _..._
- **Decision:** _..._
- **Reason:** _..._

---

## Security Considerations

- _e.g. All endpoints require JWT authentication except /health_
- _e.g. Secrets managed via GitHub Secrets / environment variables_
- _e.g. Database connections use TLS_
- _e.g. User input validated at API boundary before reaching services_

---

## Deployment

<!-- How the project is deployed. -->

| Environment | URL / Host         | Branch   | Auto-deploy? |
|-------------|--------------------|----------|--------------|
| Development | _localhost:8000_   | _any_    | No           |
| Staging     | _staging.nz..._   | _main_   | Yes          |
| Production  | _api.nz..._       | _tags_   | Manual       |
