#!/usr/bin/env python3
"""Run the existing jcode CLI in an explicit workspace and retain test evidence."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import uuid


def save(path, data):
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    with temporary.open('x', encoding='utf-8') as out:
        os.chmod(temporary, 0o600)
        json.dump(data, out, ensure_ascii=False, indent=2)
        out.flush()
        os.fsync(out.fileno())
    os.replace(temporary, path)


def execute(argv, workspace, timeout, env=None):
    proc = subprocess.Popen(argv, cwd=workspace, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, start_new_session=True, env=env)
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        stdout, stderr = proc.communicate()
        return dict(exit_code=None, status='TIMEOUT', stdout=stdout[-12000:], stderr=stderr[-4000:])
    return dict(exit_code=proc.returncode, status='SUCCESS' if proc.returncode == 0 else 'ERROR',
                stdout=stdout[-12000:], stderr=stderr[-4000:])


def run(workspace, task_id, goal, test_argv, timeout=900, coder_argv=None, engine='jcode'):
    import fcntl
    root = Path(workspace)
    if not root.is_absolute() or not root.is_dir() or not goal.strip():
        raise ValueError('Existing absolute workspace and goal required')
    root = root.resolve()
    if not isinstance(test_argv, list) or not test_argv or not all(isinstance(x, str) and x for x in test_argv):
        raise ValueError('Explicit verification argv required')
    folder = root / '.cybergene-tasks'
    folder.mkdir(mode=0o700, exist_ok=True)
    path = folder / (str(uuid.uuid5(uuid.NAMESPACE_URL, task_id)) + '.json')
    if engine not in ('jcode', 'aider'):
        raise ValueError('Unknown coding engine')
    contract = dict(task_id=task_id, goal=goal, workspace=str(root), test_argv=test_argv, engine=engine)
    digest = hashlib.sha256(json.dumps(contract, sort_keys=True).encode()).hexdigest()
    with path.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if path.exists():
            previous = json.loads(path.read_text())
            if previous['contract_hash'] != digest:
                raise ValueError('Task ID reused with changed contract')
            # Includes interrupted/unknown outcomes: no unsafe automatic re-execution.
            return previous
        state = dict(contract, contract_hash=digest, status='IN_PROGRESS',
                     steps={'delegate': 'pending', 'verify': 'pending'}, created_at=time.time())
        save(path, state)
        try:
            state['steps']['delegate'] = 'in_progress'
            save(path, state)
            coder_env = None
            if engine == 'aider':
                # Same CLI and local proxy route as the existing bridge runner.
                argv = coder_argv or [str(Path.home() / '.local/bin/aider'), '--model',
                    'openai/claude-3-5-sonnet-latest', '--message', goal, '--yes',
                    '--no-auto-commits', '--no-show-model-warnings']
                coder_env = dict(os.environ, OPENAI_API_BASE='http://127.0.0.1:8999/v1', OPENAI_API_KEY='antigravity')
                if not (root / '.git').exists() and not coder_argv:
                    argv.append('--no-git')
            else:
                argv = coder_argv or [str(Path.home() / '.local/bin/jcode'), '--provider', 'openai-compatible',
                                      '-m', 'deepseek-v4.1-flash', '--quiet', 'run', goal]
            state['delegate'] = execute(argv, root, timeout, env=coder_env)
            state['steps']['delegate'] = state['delegate']['status']
            save(path, state)
            if state['delegate']['exit_code'] != 0:
                state['status'] = state['delegate']['status']
            else:
                state['steps']['verify'] = 'in_progress'
                save(path, state)
                state['verification'] = execute(test_argv, root, timeout)
                state['steps']['verify'] = state['verification']['status']
                state['status'] = 'VERIFIED' if state['verification']['exit_code'] == 0 else state['verification']['status']
        except BaseException as exc:
            state['status'] = 'INTERRUPTED' if isinstance(exc, (KeyboardInterrupt, SystemExit)) else 'ERROR'
            state['error'] = type(exc).__name__
            save(path, state)
            raise
        state['finished_at'] = time.time()
        save(path, state)
        return state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', required=True)
    parser.add_argument('--task-id', required=True)
    parser.add_argument('--goal', required=True)
    parser.add_argument('--test-argv', required=True, help='JSON argv array; no shell interpolation')
    parser.add_argument('--engine', choices=['jcode', 'aider'], default='jcode')
    args = parser.parse_args()
    result = run(args.workspace, args.task_id, args.goal, json.loads(args.test_argv), engine=args.engine)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'VERIFIED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
