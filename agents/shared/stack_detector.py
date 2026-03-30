"""
Detect which stacks are affected by a set of changed files.
Used by the webhook handler and individual agents to apply stack-specific rules.
"""
from pathlib import PurePosixPath


STACK_EXTENSIONS = {
    "python": {".py"},
    "javascript": {".js", ".ts", ".tsx", ".jsx"},
    "tlpp": {".tlpp"},
    "docker": set(),  # detected by filename
}

STACK_PATTERNS = {
    "nodered": lambda f: "flows/" in f and f.endswith(".json"),
    "docker": lambda f: (
        PurePosixPath(f).name.startswith("Dockerfile")
        or PurePosixPath(f).name.startswith("docker-compose")
        or PurePosixPath(f).name == ".dockerignore"
    ),
}


def detect_stacks(changed_files: list[str]) -> set[str]:
    """
    Given a list of changed file paths, return the set of stacks affected.

    Returns:
        Set of stack names: "python", "javascript", "tlpp", "nodered", "docker"
    """
    stacks: set[str] = set()

    for filepath in changed_files:
        ext = PurePosixPath(filepath).suffix.lower()

        # Check extensions
        for stack, extensions in STACK_EXTENSIONS.items():
            if ext in extensions:
                stacks.add(stack)

        # Check patterns
        for stack, matcher in STACK_PATTERNS.items():
            if matcher(filepath):
                stacks.add(stack)

    return stacks


def get_files_for_stack(changed_files: list[str], stack: str) -> list[str]:
    """Filter changed files to only those belonging to a specific stack."""
    extensions = STACK_EXTENSIONS.get(stack, set())
    pattern = STACK_PATTERNS.get(stack)

    result = []
    for f in changed_files:
        ext = PurePosixPath(f).suffix.lower()
        if ext in extensions:
            result.append(f)
        elif pattern and pattern(f):
            result.append(f)

    return result
