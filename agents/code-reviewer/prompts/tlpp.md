### TLPP-Specific Review Guidelines

- Follow the domain-based folder structure: endpoint → service → validation → mapping → query
- `endpoint.tlpp` must only parse JSON and return responses — no business logic, no DB access
- `service.tlpp` orchestrates: calls validation, then mapping, then ExecAuto/query
- `validation.tlpp` checks all input before processing — return structured error arrays
- `mapping.tlpp` is the ONLY place that knows about Protheus field names (SC1, SC7, SF1, etc.)
- `query.tlpp` only exists when reads require multi-table joins or complex SQL
- Always use the shared `NzExecAuto()` wrapper — never call MsExecAuto directly
- Use `shared/rest/response.tlpp` for all HTTP responses (standardized format)
- Never hardcode company/branch codes — use `shared/protheus/environment.tlpp`
- Use structured logging via `shared/protheus/logging.tlpp`, not raw ConOut
- Function names follow: `nz{Domain}{Action}` (e.g., `nzPurchaseRequestCreate`)
- All date conversions go through `shared/protheus/dates.tlpp`
