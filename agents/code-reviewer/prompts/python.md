### Python-Specific Review Guidelines

- Use type hints on all function signatures
- Prefer Pydantic models for request/response schemas
- Use `ruff` formatting standards
- No mutable default arguments
- Use `pathlib.Path` over `os.path`
- Async endpoints should use `async def`, not `def`
- No bare `except:` — always catch specific exceptions
- Use structured logging, not `print()`
- f-strings over `.format()` or `%`
- All public functions need docstrings
