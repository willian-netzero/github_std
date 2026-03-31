"""
Test Runner Agent

Runs tests and reports coverage for each stack.
Posts a GitHub check run with pass/fail and a coverage summary comment.
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from shared.github_client import GitHubClient


def run_command(cmd: list[str], cwd: str = ".") -> tuple[int, str, str]:
    """Run a shell command and return (exit_code, stdout, stderr)."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=300,  # 5 min max
    )
    return result.returncode, result.stdout, result.stderr


def run_python_tests(repo_dir: str) -> dict:
    """Run pytest with coverage."""
    # Install deps
    run_command(["pip", "install", "-r", "requirements.txt"], cwd=repo_dir)
    run_command(["pip", "install", "pytest", "pytest-cov"], cwd=repo_dir)

    # Run tests
    code, stdout, stderr = run_command(
        ["pytest", "tests/", "--cov=src", "--cov-report=term-missing", "--cov-fail-under=70", "-v"],
        cwd=repo_dir,
    )

    # Parse coverage from output
    coverage = 0
    coverage_match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", stdout)
    if coverage_match:
        coverage = int(coverage_match.group(1))

    # Count pass/fail
    passed = len(re.findall(r"PASSED", stdout))
    failed = len(re.findall(r"FAILED", stdout))

    return {
        "stack": "python",
        "exit_code": code,
        "passed": passed,
        "failed": failed,
        "coverage": coverage,
        "output": stdout[-2000:] if len(stdout) > 2000 else stdout,
    }


def run_javascript_tests(repo_dir: str) -> dict:
    """Run Jest with coverage."""
    run_command(["npm", "ci"], cwd=repo_dir)

    code, stdout, stderr = run_command(
        ["npx", "jest", "--coverage", "--verbose"],
        cwd=repo_dir,
    )

    # Parse coverage
    coverage = 0
    cov_match = re.search(r"All files\s*\|\s*([\d.]+)", stdout)
    if cov_match:
        coverage = int(float(cov_match.group(1)))

    passed = len(re.findall(r"✓|✔|PASS", stdout))
    failed = len(re.findall(r"✗|✘|FAIL", stdout))

    return {
        "stack": "javascript",
        "exit_code": code,
        "passed": passed,
        "failed": failed,
        "coverage": coverage,
        "output": stdout[-2000:] if len(stdout) > 2000 else stdout,
    }


def run_tlpp_payload_validation(repo_dir: str) -> dict:
    """Validate TLPP JSON payloads."""
    import json
    from pathlib import Path

    payloads_dir = Path(repo_dir) / "payloads"
    if not payloads_dir.exists():
        return {
            "stack": "tlpp",
            "exit_code": 0,
            "passed": 0,
            "failed": 0,
            "coverage": 0,
            "output": "No payloads/ directory found — skipping.",
        }

    passed = 0
    failed = 0
    errors = []

    for json_file in payloads_dir.rglob("*.json"):
        try:
            with open(json_file) as f:
                json.load(f)
            passed += 1
        except json.JSONDecodeError as e:
            failed += 1
            errors.append(f"{json_file.relative_to(repo_dir)}: {e}")

    output = f"Validated {passed + failed} JSON payload(s): {passed} valid, {failed} invalid."
    if errors:
        output += "\n\nErrors:\n" + "\n".join(errors)

    return {
        "stack": "tlpp",
        "exit_code": 1 if failed > 0 else 0,
        "passed": passed,
        "failed": failed,
        "coverage": 0,
        "output": output,
    }


STACK_RUNNERS = {
    "python": run_python_tests,
    "javascript": run_javascript_tests,
    "tlpp": run_tlpp_payload_validation,
}


def run_tests(
    repo: str,
    pr_number: int,
    head_sha: str,
    changed_files: list[str],
    stacks: set[str],
) -> dict:
    """Run tests for all affected stacks and report results."""
    gh = GitHubClient(repo)

    gh.create_check_run(
        name="Test Runner",
        head_sha=head_sha,
        status="in_progress",
        title="Running tests...",
    )

    results = []
    overall_pass = True

    for stack in stacks:
        runner = STACK_RUNNERS.get(stack)
        if not runner:
            continue

        try:
            result = runner(".")
            results.append(result)
            if result["exit_code"] != 0:
                overall_pass = False
        except Exception as e:
            results.append({
                "stack": stack,
                "exit_code": 1,
                "passed": 0,
                "failed": 0,
                "coverage": 0,
                "output": f"Error running tests: {e}",
            })
            overall_pass = False

    # Build summary
    summary_lines = ["## Test Results\n"]
    for r in results:
        emoji = "✅" if r["exit_code"] == 0 else "❌"
        summary_lines.append(
            f"### {emoji} {r['stack'].title()}\n"
            f"- Passed: {r['passed']} | Failed: {r['failed']}"
        )
        if r["coverage"] > 0:
            cov_emoji = "🟢" if r["coverage"] >= 70 else "🟡" if r["coverage"] >= 50 else "🔴"
            summary_lines.append(f"- Coverage: {cov_emoji} {r['coverage']}%")
        summary_lines.append(f"\n```\n{r['output'][-1000:]}\n```\n")

    summary = "\n".join(summary_lines)

    # Post check run
    gh.create_check_run(
        name="Test Runner",
        head_sha=head_sha,
        status="completed",
        conclusion="success" if overall_pass else "failure",
        title="All tests passed" if overall_pass else "Some tests failed",
        summary=summary,
    )

    # Post comment with coverage
    marker = "<!-- agent:test-runner -->"
    comment = f"""{marker}
{summary}

---
<sub>Generated by the NetZero Test Runner agent.</sub>
"""
    gh.update_or_create_comment(pr_number, comment, marker)

    return {
        "status": "success" if overall_pass else "failure",
        "results": [{k: v for k, v in r.items() if k != "output"} for r in results],
    }
