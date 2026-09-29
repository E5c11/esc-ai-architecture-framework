---
id: ARCH-PY-ERROR
type: rules
layer: architectures
platform: [python]
architecture: python-app
requires: [ARCH-PY, CORE-ERROR, PAT-OUTCOME]
related: [ARCH-PY-ENTRYPOINT, ARCH-PY-USECASE, ARCH-PY-DATASOURCE, ARCH-PY-GATEWAY, ARCH-PY-OBSERVABILITY, PLAT-PY-TYPING]
tags: [error-handling, exceptions, outcome, result, exit-codes, two-tier, boundaries]
status: active
---
# Error Flow

## The decision

`PAT-OUTCOME` says operations whose failure is a *normal, expected* result should
return a typed result rather than throw across layer boundaries, and that programming
errors should throw. Python's idiom is exceptions, and it has no ergonomic
`Result` type. This architecture reconciles the two by separating three kinds of
"failure", each with one home:

| Kind | Example | Representation | Handled by |
|---|---|---|---|
| **Expected outcome** — a normal branch the caller must look at | a verification gate failed; a repository has validation findings; a plan needs answers | A frozen **outcome value** (`Verdict`, `ValidationReport`) returned by the use case | The entrypoint renders it; the caller branches on it |
| **Known error** — the operation could not be done, for a reason the caller can act on | task not found; plan already exists; provider not connected; malformed manifest | A typed exception deriving from one project base class (`AppError`) | Translated once, at the entrypoint |
| **Unexpected error** — a bug or an unrecoverable environment failure | `KeyError` from a logic slip; disk full; `MemoryError` | Any other exception, left to propagate | The top-level handler: log with traceback, generic message, failure status |

An outcome value is the `PAT-OUTCOME` "result" for expected branches — it is
type-checked, exhaustively renderable, and never an exception. A known error is
raised because Python callers expect `raise`/`except`, and because forcing a `Result`
through every layer would fight the language.

## Rules

```rule
id: PYERR-BASE-01
statement: All known errors MUST derive from one project base exception (`AppError`), grouped into a small hierarchy by cause (not-found, conflict, invalid-input, unavailable, ...) that entrypoints can translate without knowing individual subclasses.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PYERR-BASE-01 — All known errors MUST derive from one project base exception (`AppError`), grouped into a small hierarchy by cause (not-found, conflict, invalid-input, unavailable, ...) that entrypoints can translate without knowing individual subclasses.
```

```rule
id: PYERR-OUTCOME-01
statement: A failure that is an expected result of a normal operation (a gate failing, findings being reported) MUST be returned as a frozen outcome value, not raised as an exception.
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates PYERR-OUTCOME-01 — A failure that is an expected result of a normal operation (a gate failing, findings being reported) MUST be returned as a frozen outcome value, not raised as an exception.
```

A caller that must look at "did the gate pass?" should be unable to forget to: the
return type carries the answer.

```rule
id: PYERR-BOUNDARY-01
statement: Storage, transport, and provider exceptions MUST be translated into `AppError` subclasses at the DataSource or Gateway that produced them, chaining the original with `raise ... from`.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PYERR-BOUNDARY-01 — Storage, transport, and provider exceptions MUST be translated into `AppError` subclasses at the DataSource or Gateway that produced them, chaining the original with `raise ... from`.
```

`raise NewError(...) from exc` keeps the cause in the traceback; a bare `raise
NewError(...)` inside `except` hides it in a confusing "during handling" chain, and
`from None` discards it.

```rule
id: PYERR-SWALLOW-01
statement: Code MUST NOT use a bare `except:`, MUST NOT catch `Exception` or `BaseException` except at a top-level handler or a documented degraded-mode fallback, and MUST NOT catch an error and discard it.
type: hard
scope: error-handling
enforced_by: [ci, reviewer]
violation_message: Violates PYERR-SWALLOW-01 — Code MUST NOT use a bare `except:`, MUST NOT catch `Exception` or `BaseException` except at a top-level handler or a documented degraded-mode fallback, and MUST NOT catch an error and discard it.
```

`ruff`'s `E722`, `BLE001`, `S110`, `SIM105` enforce most of this. A deliberate
degraded-mode fallback (falling back to a cached value for a best-effort source) is
allowed *only* when the catch names the specific exception and a comment states why
(`CORE-ERROR`).

```rule
id: PYERR-CONTEXT-01
statement: A known error MUST carry enough context to act on — what was attempted, on what, and what to do next — and MUST NOT expose secrets, tokens, or raw provider payloads.
type: soft
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PYERR-CONTEXT-01 — A known error MUST carry enough context to act on — what was attempted, on what, and what to do next — and MUST NOT expose secrets, tokens, or raw provider payloads.
```

```rule
id: PYERR-TRANSLATE-01
statement: Each delivery surface MUST have one translation function mapping outcome values and `AppError` subclasses to its exit status or protocol error, plus one top-level handler for unexpected errors that logs the traceback and returns a generic failure.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PYERR-TRANSLATE-01 — Each delivery surface MUST have one translation function mapping outcome values and `AppError` subclasses to its exit status or protocol error, plus one top-level handler for unexpected errors that logs the traceback and returns a generic failure.
```

## Translating a library dependency's exceptions

A sibling library (the engine, an SDK) reports its expected failures as built-in exceptions --
`KeyError`, `FileNotFoundError`, `ValueError`, `OSError`. Left alone they reach an entrypoint
indistinguishable from a bug. Translate them **once, at the application boundary**, with a decorator on the
application operations rather than a `try`/`except` in every caller:

```python
def translates_engine_errors(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except AppError:
            raise
        except KeyError as exc:                       # str(KeyError("m")) is the repr "'m'": use the message
            raise NotFoundError(str(exc.args[0])) from exc
        except FileNotFoundError as exc:
            raise NotFoundError(str(exc)) from exc
        except (ValueError, OSError) as exc:
            raise InvalidInputError(str(exc)) from exc
    return wrapper
```

After this, an entrypoint sees either a known `AppError` or a genuine unexpected error, so its handler can catch
`AppError` and let everything else reach the top-level handler. A bare `KeyError` arriving at an entrypoint is a
bug, not "invalid input".

```rule
id: PYERR-LIBRARY-01
statement: Exceptions from a library dependency that represent expected failures MUST be translated to `AppError` at the application boundary (a decorator or a wrapper), chained with `raise ... from`; entrypoints MUST NOT catch the library's raw exception types.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PYERR-LIBRARY-01 — Exceptions from a library dependency that represent expected failures MUST be translated to `AppError` at the application boundary (a decorator or a wrapper), chained with `raise ... from`; entrypoints MUST NOT catch the library's raw exception types.
```

## Interactive loops and the translation function

An interactive flow (a menu that loops back after each action) is a second mode of the same surface. It MAY
catch `AppError` to report the message inline and continue, using the same message text; it MUST NOT catch
anything broader, and the top-level handler still covers a bug inside a flow.

## Messages and hints

Give an error a one-line message and, where useful, a separate `hint` (for example "did you mean: ...?") that the
surface renders on its own line. A message SHOULD NOT name a command of one particular surface ("run `tool
subcommand` first"); a use case is invoked from several surfaces, so carry the next step as data and let each
surface phrase it.

```rule
id: PYERR-SURFACE-01
statement: An error message raised below the entrypoint layer SHOULD NOT name a command, flag, or menu item of one delivery surface; a surface-specific next step SHOULD be carried as structured data and phrased by the surface.
type: soft
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PYERR-SURFACE-01 — An error message raised below the entrypoint layer SHOULD NOT name a command, flag, or menu item of one delivery surface; a surface-specific next step SHOULD be carried as structured data and phrased by the surface.
```

## Exit status contract (CLI)

Scripts depend on exit codes, so they are part of the public contract
(`CORE-API-STABILITY`). Define them once, document them, and do not change them casually:

| Status | Meaning |
|---|---|
| 0 | Success (including an outcome that is "nothing to do") |
| 1 | The operation could not be done (a known error) or an outcome the caller asked to be treated as failing (a gate failed) |
| 2 | Invalid usage — bad arguments (argparse's default) |
| 3 | Incomplete — more input is needed before this can proceed |
| 70+ | Unexpected internal error |

The exact table is a project decision; the rule is that it *is* a table, documented,
in one place.

```rule
id: PYERR-EXITCODE-01
statement: A project MUST document its exit-status table in one place and MUST NOT introduce exit codes outside it.
type: soft
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PYERR-EXITCODE-01 — A project MUST document its exit-status table in one place and MUST NOT introduce exit codes outside it.
```

## Assertions and programming errors

`assert` states an invariant the *programmer* believes; it is stripped under
`python -O` and MUST NOT be used to validate input or enforce a gate. Contract
violations inside the program raise (`TypeError`, `ValueError`, `RuntimeError`)
and crash fast — they are unexpected errors, not known ones.

```rule
id: PYERR-ASSERT-01
statement: `assert` MUST NOT be used for input validation or for enforcing a gate or security-relevant condition.
type: hard
scope: error-handling
enforced_by: [ci, reviewer]
violation_message: Violates PYERR-ASSERT-01 — `assert` MUST NOT be used for input validation or for enforcing a gate or security-relevant condition.
```

`ruff`'s `S101` flags `assert` outside tests.
