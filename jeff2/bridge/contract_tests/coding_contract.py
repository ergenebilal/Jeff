"""Explicit workspace and test contract for the existing Aider queue."""
from pathlib import Path


def validate_contract(workspace, files, test_argv):
    if not workspace or not Path(workspace).is_absolute():
        raise ValueError('Explicit absolute workspace required')
    root = Path(workspace).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Workspace is not a directory')
    if not isinstance(test_argv, list) or not test_argv or not all(isinstance(x, str) and x for x in test_argv):
        raise ValueError('Non-empty test argv required')
    resolved = []
    for file in files:
        candidate = (root / file).resolve()
        if not candidate.is_relative_to(root):
            raise ValueError('File escapes workspace')
        resolved.append(str(candidate))
    return str(root), resolved, test_argv
