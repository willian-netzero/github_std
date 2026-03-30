### JavaScript/TypeScript-Specific Review Guidelines

- Prefer TypeScript over JavaScript for all new code
- Use `const` by default, `let` only when reassignment is needed, never `var`
- No `any` type — use proper interfaces or generics
- React components: prefer functional components with hooks
- No direct API calls inside React components — use custom hooks or services
- No `console.log` in production code
- Handle promises properly — no unhandled rejections
- Use optional chaining (`?.`) and nullish coalescing (`??`)
- Destructure props in component signatures
- Avoid prop drilling — use context or state management for deep data
