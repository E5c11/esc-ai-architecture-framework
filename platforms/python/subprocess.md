---
id: PLAT-PY-SUBPROCESS
type: guide
layer: platforms
platform: [python]
architecture: python-app
requires: [ARCH-PY, ARCH-PY-GATEWAY, PLAT-PY]
related: [ARCH-PY-CONCURRENCY, ARCH-PY-OBSERVABILITY, PLAT-PY-TESTING]
tags: [subprocess, process, git, timeout, shell, exit-code, worktree, environment]
---
# Running Processes and Git from Python

Extends: `ARCH-PY-GATEWAY`

Running another program is the riskiest routine thing a Python program does: it can hang,
inject shell syntax, leak secrets through the environment, and return "success" the caller
misreads. Confine it to a Gateway, and make the safe form the only form.

## The one runner

Write **one** small function (in `infrastructure/gateways/process.py`) that every process
call goes through, so the rules apply once:

```python
@dataclass(frozen=True)
class ProcessResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool

def run_process(argv: Sequence[str], *, cwd: Path, timeout: float,
                env: Mapping[str, str] | None = None, max_output: int = 1_000_000) -> ProcessResult:
    try:
        completed = subprocess.run(
            list(argv), cwd=cwd, env=env, capture_output=True, text=True,
            timeout=timeout, check=False, shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        return ProcessResult(tuple(argv), -1, _clip(exc.stdout), _clip(exc.stderr), True)
    except FileNotFoundError as exc:
        raise GatewayUnavailable(f"executable not found: {argv[0]}") from exc
    return ProcessResult(tuple(argv), completed.returncode,
                         _clip(completed.stdout, max_output), _clip(completed.stderr, max_output), False)
```

## Rules

```rule
id: PYSP-RUNNER-01
statement: All process execution MUST go through one runner function in infrastructure; no other module MUST import `subprocess` (banned via `TID251`).
type: hard
scope: structure
enforced_by: [ci, reviewer]
violation_message: Violates PYSP-RUNNER-01 — All process execution MUST go through one runner function in infrastructure; no other module MUST import `subprocess` (banned via `TID251`).
```

```rule
id: PYSP-ARGV-01
statement: Commands MUST be built as argument lists with `shell=False`; a command string MUST NOT be assembled by formatting or concatenating values, and user- or model-supplied values MUST be passed only as list items (with `--` before positional values where the tool supports it).
type: hard
scope: behavior
enforced_by: [ci, reviewer]
violation_message: Violates PYSP-ARGV-01 — Commands MUST be built as argument lists with `shell=False`; a command string MUST NOT be assembled by formatting or concatenating values, and user- or model-supplied values MUST be passed only as list items (with `--` before positional values where the tool supports it).
```

```rule
id: PYSP-TIMEOUT-01
statement: The runner MUST require a timeout, MUST kill the process (and its children where applicable) on expiry, and MUST report expiry as data (`timed_out`), not as an unhandled exception.
type: hard
scope: behavior
enforced_by: [ci, reviewer]
violation_message: Violates PYSP-TIMEOUT-01 — The runner MUST require a timeout, MUST kill the process (and its children where applicable) on expiry, and MUST report expiry as data (`timed_out`), not as an unhandled exception.
```

```rule
id: PYSP-RESULT-01
statement: The runner MUST return the exit status and captured output and MUST NOT interpret them; whether a return code means pass or fail MUST be decided by the caller, and `check=True` MUST NOT be used to smuggle that decision into an exception.
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates PYSP-RESULT-01 — The runner MUST return the exit status and captured output and MUST NOT interpret them; whether a return code means pass or fail MUST be decided by the caller, and `check=True` MUST NOT be used to smuggle that decision into an exception.
```

```rule
id: PYSP-ENV-01
statement: Where secrets exist in the parent environment, the runner MUST pass an explicit environment built from an allow-list rather than inheriting everything.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYSP-ENV-01 — Where secrets exist in the parent environment, the runner MUST pass an explicit environment built from an allow-list rather than inheriting everything.
```

```rule
id: PYSP-CWD-01
statement: The runner MUST take an explicit `cwd`; a process MUST NOT depend on the parent's current directory, and `os.chdir` MUST NOT be used.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYSP-CWD-01 — The runner MUST take an explicit `cwd`; a process MUST NOT depend on the parent's current directory, and `os.chdir` MUST NOT be used.
```

`os.chdir` is process-global state: it breaks concurrent work and every test that runs
after it.

## Git

Drive git through the same runner: `["git", "-C", str(repo), ...]`. A GitPython or
libgit2 dependency is unnecessary for the handful of operations most programs need.

- **Isolate effects in a worktree** (`git worktree add`) on a task-named branch, run the
  work there, and merge back in a separate explicit step (`PYGW-ISOLATE-01`). A failed
  run leaves the worktree as a resumable checkpoint.
- **Never rewrite or discard history** the program did not create: no force-push, no
  `reset --hard` of a user's checkout, no `--no-verify`, unless the user explicitly asks.
- **Read state with plumbing/porcelain flags** meant for machines (`--porcelain`,
  `-z`, `rev-parse`), not by parsing human output.
- **Exclude program-owned directories locally** through `.git/info/exclude`, not by
  editing the user's tracked `.gitignore`.

```rule
id: PYSP-GIT-01
statement: Git operations MUST use machine-readable output modes, MUST NOT run history-rewriting or history-discarding commands against a user's checkout without an explicit request, and MUST NOT modify tracked ignore files to hide program-owned directories.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYSP-GIT-01 — Git operations MUST use machine-readable output modes, MUST NOT run history-rewriting or history-discarding commands against a user's checkout without an explicit request, and MUST NOT modify tracked ignore files to hide program-owned directories.
```

## Testing

Test the runner against a trivial real process (`[sys.executable, "-c", "..."]`) for exit
status, output capture, timeout, and missing executable. Test git operations against a
temporary repository created with real `git init` in `tmp_path`; never against the
developer's repositories (`PYTEST-ISOLATE-01`).
