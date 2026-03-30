"""
NetZero Agent Orchestrator — Webhook Handler

Receives GitHub webhook events and dispatches the appropriate agents.
Deploy as a Docker container or use as a GitHub App.

Environment variables:
    GITHUB_TOKEN        — GitHub PAT or App installation token
    GITHUB_REPO         — e.g. "netzero-hq/svc-carbon-api"
    WEBHOOK_SECRET      — GitHub webhook secret for signature verification
    ANTHROPIC_API_KEY   — Claude API key (for AI-powered agents)
"""
import hashlib
import hmac
import json
import os
import asyncio
import logging
from typing import Any

from fastapi import FastAPI, Request, HTTPException
import httpx

# Agent imports (same package)
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from shared.github_client import GitHubClient
from shared.stack_detector import detect_stacks

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("orchestrator")

app = FastAPI(title="NetZero Agent Orchestrator")

WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")


# ── Webhook Signature Verification ───────────────────────────────

def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify the GitHub webhook HMAC-SHA256 signature."""
    if not WEBHOOK_SECRET:
        logger.warning("WEBHOOK_SECRET not set — skipping signature check")
        return True
    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


# ── Agent Dispatch ───────────────────────────────────────────────

async def dispatch_agent(agent_name: str, func, *args, **kwargs):
    """Run an agent function and log the result."""
    try:
        logger.info(f"Dispatching agent: {agent_name}")
        result = await asyncio.to_thread(func, *args, **kwargs)
        logger.info(f"Agent {agent_name} completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Agent {agent_name} failed: {e}")
        return {"error": str(e)}


# ── Event Handlers ───────────────────────────────────────────────

async def handle_pr_opened(payload: dict):
    """Handle pull_request.opened and pull_request.synchronize events."""
    pr = payload["pull_request"]
    pr_number = pr["number"]
    head_sha = pr["head"]["sha"]
    repo = payload["repository"]["full_name"]

    gh = GitHubClient(repo)

    # Get changed files
    files_data = gh.get_pr_files(pr_number)
    changed_files = [f["filename"] for f in files_data]
    stacks = detect_stacks(changed_files)

    logger.info(
        f"PR #{pr_number} — {len(changed_files)} files changed, stacks: {stacks}"
    )

    # Import agent functions
    from architecture_guard.check import run_architecture_check
    from code_reviewer.review import run_code_review
    from test_runner.run import run_tests
    from security_scanner.scan import run_security_scan
    from pr_summarizer.summarize import run_pr_summary

    # Always run these agents in parallel
    tasks = [
        dispatch_agent("Architecture Guard", run_architecture_check, repo, pr_number, head_sha, changed_files, stacks),
        dispatch_agent("Code Reviewer", run_code_review, repo, pr_number, head_sha, changed_files, stacks),
        dispatch_agent("Security Scanner", run_security_scan, repo, pr_number, head_sha, changed_files, stacks),
    ]

    # Only on open (not sync) — generate summary
    if payload.get("action") == "opened":
        tasks.append(
            dispatch_agent("PR Summarizer", run_pr_summary, repo, pr_number, head_sha, changed_files, stacks)
        )

    # Test runner (only if test-related stacks)
    # Note: TLPP structural checks are handled by Architecture Guard (stack-aware rules)
    testable_stacks = stacks & {"python", "javascript", "nodered"}
    if testable_stacks:
        tasks.append(
            dispatch_agent("Test Runner", run_tests, repo, pr_number, head_sha, changed_files, testable_stacks)
        )

    # Run all agents in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    logger.info(f"All agents completed for PR #{pr_number}")
    return results


# ── Webhook Endpoint ─────────────────────────────────────────────

@app.post("/webhook")
async def webhook(request: Request):
    """Receive GitHub webhook events."""
    payload_bytes = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not verify_signature(payload_bytes, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    event = request.headers.get("X-GitHub-Event", "")
    payload = json.loads(payload_bytes)
    action = payload.get("action", "")

    logger.info(f"Received event: {event}.{action}")

    if event == "pull_request" and action in ("opened", "synchronize"):
        asyncio.create_task(handle_pr_opened(payload))
        return {"status": "dispatched"}

    if event == "issue_comment" and action == "created":
        # Check if the comment mentions the bot
        comment_body = payload.get("comment", {}).get("body", "")
        if "@netzero-bot" in comment_body.lower():
            logger.info("Bot mentioned in comment — triggering code review")
            # Re-trigger code review
            return {"status": "review-triggered"}

    return {"status": "ignored", "event": f"{event}.{action}"}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "netzero-agent-orchestrator"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
