---
id: PLAT-PY-MCP
type: guide
layer: platforms
platform: [python]
architecture: python-app
requires: [ARCH-PY, ARCH-PY-ENTRYPOINT, PLAT-PY, PLAT-PY-TYPING]
related: [ARCH-PY-ERROR, ARCH-PY-POLICY, ARCH-PY-CONCURRENCY, ARCH-PY-OBSERVABILITY, PLAT-PY-CLI]
tags: [mcp, model-context-protocol, tools, server, stdio, schema, tool-error]
---
# MCP Server Surface

Extends: `ARCH-PY-ENTRYPOINT`

A Model Context Protocol server exposes the program's capabilities as **tools** an AI
client can call. It is an entrypoint like any other: the tools are thin, the logic is in
the use cases, and adding the server must not change a line of application code — if it
does, the logic was in the wrong place (`ARCH-PY`, "One logic, many surfaces").

## SDK version

The official Python SDK is the `mcp` package. **Its API changed at 2.0**: what v1 called
`FastMCP` (`from mcp.server.fastmcp import FastMCP`) is `MCPServer` in v2
(`from mcp.server.mcpserver import MCPServer`). Pin the major version in
`pyproject.toml` and write code against the version you pin; do not copy snippets
across majors. The shape below was run against `mcp` 2.2.

```python
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

def build_server(app: App) -> MCPServer:
    server = MCPServer("escape-ai")

    @server.tool()
    def escape_fix(objective: str, repository: str) -> dict:
        """Draft a fix initiative for `objective` in `repository`."""
        try:
            draft = app.draft_plan(DraftRequest.for_intent("fix", objective, repository))
        except AppError as exc:
            raise ToolError(str(exc)) from exc
        return render_draft_json(draft)

    return server
```

`server.run()` defaults to the `stdio` transport; `streamable-http` and `sse` are
selectable. Tool input schemas are generated from the function's type hints and
docstring, which is why annotations on tool functions are part of the public contract.

## Rules

```rule
id: PYMCP-THIN-01
statement: An MCP tool function MUST parse its typed arguments, call exactly one use case, and translate the result; it MUST contain no business logic and MUST NOT call another surface.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYMCP-THIN-01 — An MCP tool function MUST parse its typed arguments, call exactly one use case, and translate the result; it MUST contain no business logic and MUST NOT call another surface.
```

```rule
id: PYMCP-VOCAB-01
statement: Tool names and parameters MUST come from the same intent vocabulary and procedure definitions as the other surfaces (one tool per intent verb or use case); a tool MUST NOT invent an operation, stage, or shortcut the CLI does not have.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYMCP-VOCAB-01 — Tool names and parameters MUST come from the same intent vocabulary and procedure definitions as the other surfaces (one tool per intent verb or use case); a tool MUST NOT invent an operation, stage, or shortcut the CLI does not have.
```

A capability that appears only over MCP is a second product. The mapping from tool to
use case is data, tested for coverage against the use-case list.

```rule
id: PYMCP-SCHEMA-01
statement: Every tool parameter MUST have a precise type (enums for closed choices, not free strings) and a description; return values MUST be structured, documented shapes.
type: hard
scope: return-type
enforced_by: [ci, reviewer]
violation_message: Violates PYMCP-SCHEMA-01 — Every tool parameter MUST have a precise type (enums for closed choices, not free strings) and a description; return values MUST be structured, documented shapes.
```

```rule
id: PYMCP-ERROR-01
statement: Known errors MUST be raised as the SDK's tool error (`ToolError`) with a message the client can act on; unexpected errors MUST be logged with a traceback to the server log and reported generically, never with internals.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PYMCP-ERROR-01 — Known errors MUST be raised as the SDK's tool error (`ToolError`) with a message the client can act on; unexpected errors MUST be logged with a traceback to the server log and reported generically, never with internals.
```

```rule
id: PYMCP-STDIO-01
statement: On the stdio transport the process's stdout carries protocol messages only; nothing else MUST write to stdout, and all logging and diagnostics MUST go to stderr or a file.
type: hard
scope: behavior
enforced_by: [ci, reviewer]
violation_message: Violates PYMCP-STDIO-01 — On the stdio transport the process's stdout carries protocol messages only; nothing else MUST write to stdout, and all logging and diagnostics MUST go to stderr or a file.
```

A stray `print()` corrupts the protocol stream. This is one more reason `print` is banned
below the CLI entrypoint (`PYEP-IO-01`).

```rule
id: PYMCP-MANDATORY-01
statement: A tool MUST NOT offer a parameter that skips, weakens, or auto-approves a mandatory stage or gate; an automated caller runs the same procedure as a human one.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYMCP-MANDATORY-01 — A tool MUST NOT offer a parameter that skips, weakens, or auto-approves a mandatory stage or gate; an automated caller runs the same procedure as a human one.
```

`ARCH-PY-POLICY` still applies: an MCP client's stages that would ask a human either use
the protocol's elicitation mechanism through a `Prompter` implementation, or return an
"input needed" outcome the client can answer in a follow-up call — never an implicit
approval.

```rule
id: PYMCP-EFFECT-01
statement: A tool that writes files, runs processes, or changes durable state MUST be declared as such in its tool annotations and MUST preview or require an explicit confirming argument, matching the CLI's preview-by-default behavior.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYMCP-EFFECT-01 — A tool that writes files, runs processes, or changes durable state MUST be declared as such in its tool annotations and MUST preview or require an explicit confirming argument, matching the CLI's preview-by-default behavior.
```

## Concurrency

MCP servers are typically async at the transport. Keep use cases synchronous and bridge
at the tool boundary with `asyncio.to_thread` where a use case blocks
(`PYCONC-COLOR-01`); do not turn the application layer async to suit one surface.
