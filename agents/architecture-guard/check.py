"""
Architecture Guard Agent

Validates that layer separation rules are respected across all stacks.
Posts a GitHub check run with success/failure and inline annotations
on the exact lines that violate the rules.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from shared.github_client import GitHubClient


# ── Rule Definitions ─────────────────────────────────────────────

RULES = {
    "python": [
        {
            "name": "API layer must not import repositories or ORM",
            "paths": ["src/api/"],
            "pattern": r"(?:from\s+.*(?:repositories|sqlalchemy|models\.entities).*import|import\s+(?:sqlalchemy|models\.entities))",
            "message": "API layer must not import from repositories or ORM directly. Use services instead.",
        },
        {
            "name": "Domain must not import API",
            "paths": ["src/models/"],
            "pattern": r"from\s+.*api.*import",
            "message": "Domain layer must not import from API layer. Dependencies flow inward.",
        },
        {
            "name": "No hardcoded secrets",
            "paths": ["src/"],
            "pattern": r"""(?:api_key|secret|password|token)\s*=\s*["'][^"']{8,}["']""",
            "message": "Possible hardcoded secret. Use environment variables instead.",
        },
    ],
    "javascript": [
        {
            "name": "Components must not make direct API calls",
            "paths": ["src/components/"],
            "pattern": r"(?:fetch\(|axios\.|\.get\(|\.post\(|\.put\(|\.delete\()",
            "message": "Components must not make direct API calls. Use services/ or hooks/.",
            "exclude_pattern": r"(?:\.test\.|\.spec\.)",
        },
        {
            "name": "No console.log in production code",
            "paths": ["src/"],
            "pattern": r"console\.(?:log|debug)\(",
            "message": "Remove console.log/debug from production code.",
            "exclude_pattern": r"(?:\.test\.|\.spec\.|// allowed)",
        },
    ],
    "tlpp": [
        {
            "name": "Endpoint must not contain DB operations",
            "paths": ["src/"],
            "file_match": r"endpoint\.tlpp$",
            "pattern": r"(?:DbSelectArea|RecLock|MsExecAuto|MATA\d{3})",
            "message": "endpoint.tlpp must not contain DB operations or ExecAuto calls. Move to service.tlpp.",
        },
        {
            "name": "No hardcoded Protheus credentials",
            "paths": ["src/"],
            "pattern": r"""(?:cPassword|cToken|cSenha)\s*:=\s*["'][^"']+["']""",
            "message": "Hardcoded credentials detected. Use environment configuration.",
        },
    ],
}


# ── Rule Checker ─────────────────────────────────────────────────

def check_file_against_rules(
    filepath: str, content: str, stack: str
) -> list[dict]:
    """
    Check a single file against the rules for a given stack.

    Returns:
        List of annotation dicts: {path, line, message, rule_name}
    """
    violations = []
    stack_rules = RULES.get(stack, [])

    for rule in stack_rules:
        # Check if file is in the relevant paths
        path_match = any(filepath.startswith(p) for p in rule["paths"])
        if not path_match:
            continue

        # Check file_match pattern (for TLPP endpoint-specific rules)
        if "file_match" in rule:
            if not re.search(rule["file_match"], filepath):
                continue

        # Check each line
        for line_num, line in enumerate(content.split("\n"), start=1):
            # Skip excluded patterns
            if "exclude_pattern" in rule:
                if re.search(rule["exclude_pattern"], line):
                    continue

            if re.search(rule["pattern"], line, re.IGNORECASE):
                violations.append({
                    "path": filepath,
                    "start_line": line_num,
                    "end_line": line_num,
                    "annotation_level": "failure",
                    "message": f"[{rule['name']}] {rule['message']}",
                })

    return violations


# ── Main Agent Function ──────────────────────────────────────────

def run_architecture_check(
    repo: str,
    pr_number: int,
    head_sha: str,
    changed_files: list[str],
    stacks: set[str],
) -> dict:
    """
    Run architecture checks on all changed files and report results.

    Posts a GitHub check run with success/failure and inline annotations.
    """
    gh = GitHubClient(repo)

    # Start the check run
    check = gh.create_check_run(
        name="Architecture Guard",
        head_sha=head_sha,
        status="in_progress",
        title="Checking layer separation...",
        summary="Analyzing changed files for architecture violations.",
    )

    all_violations = []

    for filepath in changed_files:
        # Determine which stack this file belongs to
        file_stacks = set()
        if filepath.endswith(".py"):
            file_stacks.add("python")
        elif filepath.endswith((".ts", ".tsx", ".js", ".jsx")):
            file_stacks.add("javascript")
        elif filepath.endswith(".tlpp"):
            file_stacks.add("tlpp")

        for stack in file_stacks:
            try:
                content = gh.get_file_content(filepath, head_sha)
                violations = check_file_against_rules(filepath, content, stack)
                all_violations.extend(violations)
            except Exception as e:
                # File might be deleted — skip
                continue

    # Report results
    if all_violations:
        summary_lines = [
            f"Found **{len(all_violations)} architecture violation(s)**:\n",
        ]
        for v in all_violations:
            summary_lines.append(f"- `{v['path']}` line {v['start_line']}: {v['message']}")

        gh.create_check_run(
            name="Architecture Guard",
            head_sha=head_sha,
            status="completed",
            conclusion="failure",
            title=f"{len(all_violations)} layer violation(s) found",
            summary="\n".join(summary_lines),
            annotations=all_violations[:50],
        )
        return {"status": "failure", "violations": len(all_violations)}
    else:
        gh.create_check_run(
            name="Architecture Guard",
            head_sha=head_sha,
            status="completed",
            conclusion="success",
            title="No architecture violations",
            summary="All changed files respect the layer separation rules.",
        )
        return {"status": "success", "violations": 0}
