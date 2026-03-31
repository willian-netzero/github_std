"""
GitHub API client for agent communication.
All agents use this module to post comments, create check runs, and add labels.
"""
import os
import json
import httpx
from typing import Optional


GITHUB_API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


class GitHubClient:
    def __init__(self, repo: str):
        """
        Args:
            repo: Full repo name, e.g. "netzero-hq/svc-carbon-api"
        """
        self.repo = repo
        self.client = httpx.Client(
            base_url=GITHUB_API,
            headers=HEADERS,
            timeout=30.0,
        )

    # ── PR Comments ──────────────────────────────────────────────

    def post_comment(self, pr_number: int, body: str) -> dict:
        """Post a comment on a PR."""
        url = f"/repos/{self.repo}/issues/{pr_number}/comments"
        resp = self.client.post(url, json={"body": body})
        resp.raise_for_status()
        return resp.json()

    def post_review_comment(
        self,
        pr_number: int,
        body: str,
        commit_sha: str,
        path: str,
        line: int,
        side: str = "RIGHT",
    ) -> dict:
        """Post an inline review comment on a specific line."""
        url = f"/repos/{self.repo}/pulls/{pr_number}/comments"
        resp = self.client.post(
            url,
            json={
                "body": body,
                "commit_id": commit_sha,
                "path": path,
                "line": line,
                "side": side,
            },
        )
        resp.raise_for_status()
        return resp.json()

    def update_or_create_comment(
        self, pr_number: int, body: str, marker: str
    ) -> dict:
        """
        Update an existing comment (identified by a hidden marker) or create a new one.
        The marker is a hidden HTML comment like <!-- agent:pr-summarizer -->
        """
        comments = self.list_comments(pr_number)
        for comment in comments:
            if marker in comment.get("body", ""):
                return self.update_comment(comment["id"], body)
        return self.post_comment(pr_number, body)

    def list_comments(self, pr_number: int) -> list[dict]:
        url = f"/repos/{self.repo}/issues/{pr_number}/comments"
        resp = self.client.get(url)
        resp.raise_for_status()
        return resp.json()

    def update_comment(self, comment_id: int, body: str) -> dict:
        url = f"/repos/{self.repo}/issues/comments/{comment_id}"
        resp = self.client.patch(url, json={"body": body})
        resp.raise_for_status()
        return resp.json()

    # ── Check Runs ───────────────────────────────────────────────

    def create_check_run(
        self,
        name: str,
        head_sha: str,
        status: str = "in_progress",
        conclusion: Optional[str] = None,
        title: str = "",
        summary: str = "",
        annotations: Optional[list[dict]] = None,
    ) -> dict:
        """
        Create or complete a check run.

        Args:
            name: Check name, e.g. "Architecture Guard"
            head_sha: Commit SHA
            status: "queued", "in_progress", or "completed"
            conclusion: Required when status=completed.
                        "success", "failure", "neutral", "cancelled"
            title: Short title for the check output
            summary: Markdown summary
            annotations: List of annotation dicts with keys:
                         path, start_line, end_line, annotation_level, message
        """
        url = f"/repos/{self.repo}/check-runs"
        payload: dict = {
            "name": name,
            "head_sha": head_sha,
            "status": status,
        }
        if conclusion:
            payload["conclusion"] = conclusion
        if title or summary:
            payload["output"] = {
                "title": title or name,
                "summary": summary or "",
            }
            if annotations:
                payload["output"]["annotations"] = annotations[:50]  # API limit
        resp = self.client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()

    # ── PR Diff ──────────────────────────────────────────────────

    def get_pr_diff(self, pr_number: int) -> str:
        """Get the raw diff for a PR."""
        url = f"/repos/{self.repo}/pulls/{pr_number}"
        resp = self.client.get(
            url, headers={**HEADERS, "Accept": "application/vnd.github.diff"}
        )
        resp.raise_for_status()
        return resp.text

    def get_pr_files(self, pr_number: int) -> list[dict]:
        """Get list of changed files in a PR."""
        url = f"/repos/{self.repo}/pulls/{pr_number}/files"
        resp = self.client.get(url)
        resp.raise_for_status()
        return resp.json()

    # ── Labels ───────────────────────────────────────────────────

    def add_labels(self, pr_number: int, labels: list[str]) -> dict:
        url = f"/repos/{self.repo}/issues/{pr_number}/labels"
        resp = self.client.post(url, json={"labels": labels})
        resp.raise_for_status()
        return resp.json()

    # ── File Contents ────────────────────────────────────────────

    def get_file_content(self, path: str, ref: str) -> str:
        """Get the content of a file at a specific ref (branch/sha)."""
        url = f"/repos/{self.repo}/contents/{path}"
        resp = self.client.get(url, params={"ref": ref})
        resp.raise_for_status()
        data = resp.json()
        import base64
        return base64.b64decode(data["content"]).decode("utf-8")
