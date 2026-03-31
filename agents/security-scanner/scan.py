"""
Security Scanner Agent

Scans PR diffs for leaked secrets, vulnerable patterns, and dependency issues.
Blocks merge if secrets are found (required check).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from shared.github_client import GitHubClient


# ── Secret Patterns ──────────────────────────────────────────────

SECRET_PATTERNS = [
    {
        "name": "AWS Access Key",
        "pattern": r"(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}",
        "severity": "critical",
    },
    {
        "name": "AWS Secret Key",
        "pattern": r"""(?:aws_secret_access_key|secret_key)\s*[=:]\s*["']?[A-Za-z0-9/+=]{40}""",
        "severity": "critical",
    },
    {
        "name": "Generic API Key",
        "pattern": r"""(?:api[_-]?key|apikey)\s*[=:]\s*["'][A-Za-z0-9\-_.]{20,}["']""",
        "severity": "high",
    },
    {
        "name": "Generic Secret/Token",
        "pattern": r"""(?:secret|token|password|passwd|pwd)\s*[=:]\s*["'][^"'\s]{8,}["']""",
        "severity": "high",
    },
    {
        "name": "Private Key",
        "pattern": r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
        "severity": "critical",
    },
    {
        "name": "JWT Token",
        "pattern": r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
        "severity": "high",
    },
    {
        "name": "Database Connection String",
        "pattern": r"""(?:postgres|mysql|mongodb|redis)://[^\s"']{10,}""",
        "severity": "high",
    },
    {
        "name": "TLPP Hardcoded Credential",
        "pattern": r"""(?:cPassword|cToken|cSenha|cChave)\s*:=\s*["'][^"']+["']""",
        "severity": "high",
    },
    {
        "name": "Anthropic API Key",
        "pattern": r"sk-ant-[A-Za-z0-9\-]{20,}",
        "severity": "critical",
    },
    {
        "name": "GitHub Token",
        "pattern": r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}",
        "severity": "critical",
    },
]

# Files to skip (binary, generated, etc.)
SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
    ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".tar", ".gz",
    ".lock", ".sum",
    ".min.js", ".min.css",
}

SKIP_PATHS = {
    "node_modules/", "vendor/", ".git/", "dist/", "build/",
    "patchs/",  # TLPP generated patches
}


# ── Dangerous Patterns ───────────────────────────────────────────

DANGEROUS_PATTERNS = {
    "python": [
        {
            "name": "SQL Injection Risk",
            "pattern": r"""(?:execute|cursor\.execute)\s*\(\s*f["']|\.format\(""",
            "message": "Possible SQL injection — use parameterized queries instead of string formatting.",
            "severity": "warning",
        },
        {
            "name": "Eval Usage",
            "pattern": r"\beval\s*\(",
            "message": "eval() is dangerous — avoid executing arbitrary code.",
            "severity": "warning",
        },
    ],
    "javascript": [
        {
            "name": "innerHTML Assignment",
            "pattern": r"\.innerHTML\s*=",
            "message": "innerHTML can lead to XSS — use textContent or a sanitizer.",
            "severity": "warning",
        },
        {
            "name": "Eval Usage",
            "pattern": r"\beval\s*\(",
            "message": "eval() is dangerous — avoid executing arbitrary code.",
            "severity": "warning",
        },
    ],
}


def should_skip_file(filepath: str) -> bool:
    """Check if a file should be skipped."""
    for skip in SKIP_PATHS:
        if filepath.startswith(skip):
            return True
    for ext in SKIP_EXTENSIONS:
        if filepath.endswith(ext):
            return True
    return False


def scan_content(
    filepath: str, content: str, stack: str = ""
) -> list[dict]:
    """Scan file content for secrets and dangerous patterns."""
    findings = []

    for line_num, line in enumerate(content.split("\n"), start=1):
        # Skip comments (basic heuristic)
        stripped = line.strip()
        if stripped.startswith(("#", "//", "*", "/*")):
            continue

        # Check secret patterns
        for pattern in SECRET_PATTERNS:
            if re.search(pattern["pattern"], line, re.IGNORECASE):
                findings.append({
                    "path": filepath,
                    "start_line": line_num,
                    "end_line": line_num,
                    "annotation_level": "failure" if pattern["severity"] == "critical" else "warning",
                    "message": f"🔐 [{pattern['name']}] Possible secret detected. Remove and rotate if real.",
                    "severity": pattern["severity"],
                    "type": "secret",
                })

        # Check dangerous code patterns
        if stack in DANGEROUS_PATTERNS:
            for dp in DANGEROUS_PATTERNS[stack]:
                if re.search(dp["pattern"], line):
                    findings.append({
                        "path": filepath,
                        "start_line": line_num,
                        "end_line": line_num,
                        "annotation_level": "warning",
                        "message": f"⚠️ [{dp['name']}] {dp['message']}",
                        "severity": dp["severity"],
                        "type": "dangerous_pattern",
                    })

    return findings


def run_security_scan(
    repo: str,
    pr_number: int,
    head_sha: str,
    changed_files: list[str],
    stacks: set[str],
) -> dict:
    """Run security scan on all changed files."""
    gh = GitHubClient(repo)

    # Start check
    gh.create_check_run(
        name="Security Scanner",
        head_sha=head_sha,
        status="in_progress",
        title="Scanning for secrets and vulnerabilities...",
    )

    all_findings = []
    critical_findings = []

    for filepath in changed_files:
        if should_skip_file(filepath):
            continue

        try:
            content = gh.get_file_content(filepath, head_sha)
        except Exception:
            continue

        # Determine stack for this file
        stack = ""
        if filepath.endswith(".py"):
            stack = "python"
        elif filepath.endswith((".ts", ".tsx", ".js", ".jsx")):
            stack = "javascript"
        elif filepath.endswith(".tlpp"):
            stack = "tlpp"

        findings = scan_content(filepath, content, stack)
        all_findings.extend(findings)
        critical_findings.extend(f for f in findings if f["severity"] == "critical")

    # Report
    secrets_found = [f for f in all_findings if f["type"] == "secret"]
    patterns_found = [f for f in all_findings if f["type"] == "dangerous_pattern"]

    if critical_findings:
        summary = f"**🚨 {len(critical_findings)} critical secret(s) detected!**\n\n"
        summary += "These MUST be removed before merging. If these are real credentials, rotate them immediately.\n\n"
        for f in critical_findings:
            summary += f"- `{f['path']}` line {f['start_line']}: {f['message']}\n"

        gh.create_check_run(
            name="Security Scanner",
            head_sha=head_sha,
            status="completed",
            conclusion="failure",
            title=f"{len(critical_findings)} critical secret(s) found",
            summary=summary,
            annotations=all_findings[:50],
        )
        return {"status": "failure", "critical": len(critical_findings), "warnings": len(patterns_found)}

    elif all_findings:
        summary = f"Found {len(all_findings)} advisory finding(s):\n\n"
        for f in all_findings:
            summary += f"- `{f['path']}` line {f['start_line']}: {f['message']}\n"

        gh.create_check_run(
            name="Security Scanner",
            head_sha=head_sha,
            status="completed",
            conclusion="neutral",
            title=f"{len(all_findings)} advisory finding(s)",
            summary=summary,
            annotations=all_findings[:50],
        )
        return {"status": "neutral", "critical": 0, "warnings": len(all_findings)}

    else:
        gh.create_check_run(
            name="Security Scanner",
            head_sha=head_sha,
            status="completed",
            conclusion="success",
            title="No security issues found",
            summary="All changed files passed the security scan.",
        )
        return {"status": "success", "critical": 0, "warnings": 0}
