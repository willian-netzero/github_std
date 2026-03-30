# Security

> Security policies and practices for this project.
> Every contributor must follow these rules. No exceptions.

**Last updated:** _YYYY-MM-DD_

---

## Golden Rules

1. **Never commit secrets.** No API keys, tokens, passwords, or connection strings in code.
2. **Never trust user input.** Validate and sanitize everything at the boundary.
3. **Never run as root.** Docker containers use non-root users. Services use least-privilege.
4. **Never skip dependency audits.** CI blocks merge when critical vulnerabilities are found.
5. **Never log sensitive data.** Mask PII, tokens, and credentials in all log output.

---

## Secret Management

| Environment  | Method                                   |
|--------------|------------------------------------------|
| Local dev    | `.env` file (never committed, in `.gitignore`) |
| CI/CD        | GitHub Actions Secrets                   |
| Staging/Prod | _e.g. Vault, AWS Secrets Manager, K8s Secrets_ |

### What counts as a secret

- API keys and tokens (including internal service tokens)
- Database connection strings
- JWT signing keys
- OAuth client secrets
- SSH keys and certificates
- Any credential that grants access to a system

### If a secret is accidentally committed

1. **Immediately rotate the secret** — consider it compromised
2. Notify the team lead
3. Remove it from git history using `git filter-repo` or `BFG Repo Cleaner`
4. Add a `.gitignore` rule to prevent recurrence
5. Document the incident

---

## Authentication & Authorization

<!-- Describe how auth works in this project. -->

- _e.g. JWT tokens with refresh rotation_
- _e.g. Role-based access control (RBAC)_
- _e.g. API key authentication for service-to-service_

---

## Input Validation

- All external input is validated at the **API/endpoint layer** before reaching services
- Use schema validation (_Pydantic for Python, Zod/Yup for JS/TS_)
- Reject invalid input with clear error messages (400/422 responses)
- Never construct SQL with string formatting — use parameterized queries
- File uploads must be validated for type, size, and content

---

## Dependency Security

- CI runs `pip audit` (Python) / `npm audit` (JS/TS) on every PR
- Critical vulnerabilities **block merge**
- Dependencies are updated regularly (at least monthly)
- Only use well-maintained, reputable packages
- Pin dependency versions — no `latest` or wildcard versions in production

---

## Docker Security

- Base images must use specific version tags (no `:latest`)
- Run as non-root user (`USER 1001` in Dockerfile)
- Multi-stage builds to minimize image size and attack surface
- No secrets in Dockerfile or docker-compose files
- Health checks must be defined
- Scan images with `trivy` or `docker scout` before deploy

---

## Logging & Monitoring

### What to log

- Request/response metadata (method, path, status, duration)
- Business events (user actions, state transitions)
- Errors with stack traces and context

### What NOT to log

- Passwords or tokens (even partially)
- Full credit card numbers
- Personal data (email, phone) — mask if needed for debugging
- Request/response bodies containing sensitive fields

---

## Incident Response

If you discover a security issue:

1. **Do not discuss in public channels** (Slack, GitHub issues)
2. Notify the security contact: _@security-lead / security@netzero.green_
3. Document: what, when, how discovered, potential impact
4. Fix in a private branch, merge via PR with minimal description
5. Post-mortem after resolution

---

## Compliance Notes

<!-- If applicable, list relevant compliance requirements. -->

- _e.g. LGPD (Brazilian data protection)_
- _e.g. ISO 27001_
- _e.g. SOC 2_
