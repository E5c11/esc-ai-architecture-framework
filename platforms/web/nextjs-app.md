---
id: PLAT-WEB-NEXT-APP
type: guide
layer: platforms
platform: [web]
architecture: [web-app]
requires: [PLAT-WEB-NEXT, ARCH-WEB-APP, ARCH-WEB-APP-ERR-CLASSES]
related: [PLAT-WEB-HTTP, PLAT-WEB-NEXT-APP-DEPLOY, QG-WEB-TESTING]
tags: [nextjs, server-actions, route-handlers, revalidation, outcome, error-digest]
---

# Next.js for `web-app`: Server Actions, Route Handlers, Revalidation

Extends: `PLAT-WEB-NEXT`, `ARCH-WEB-APP`

This doc covers the Next.js mechanics specific to `web-app`'s Route
Handler/Server Action boundary — the concrete platform behavior
`ARCH-WEB-APP`'s layer contracts assume but don't themselves depend on
Next.js to state.

## Return, don't throw

`ARCH-WEB-APP-ERR-CLASSES` flagged and deliberately deferred this fact to
this doc: Next.js strips a thrown Server Action error down to an opaque
digest string in production — the client sees neither the message nor the
stack, only something like `Error: An error occurred in the Server
Components render. ... digest: "1234567890"`. Throwing is how you lose the
failure detail `ARCH-WEB-APP-ERR-UNKNOWN-01` requires you to keep.

```rule
id: PLAT-WEB-NEXT-APP-THROW-01
statement: A Server Action MUST return an `Outcome`-shaped result for every expected failure — it MUST NOT `throw` for a failure the caller is meant to handle.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-APP-THROW-01 — Next.js strips a thrown Server Action error to an opaque digest in production; return an explicit Outcome instead (see ARCH-WEB-APP-ERR-UNKNOWN-01).
```

```typescript
// ❌ Wrong — production caller sees only an opaque digest
'use server';
export async function updateQuestion(input: UpdateQuestionInput) {
  const question = await questionsProvider.update(input);
  if (!question) throw new Error('Question not found');
  return question;
}

// ✅ Correct — the caller always gets a typed, inspectable result
'use server';
export async function updateQuestion(
  input: UpdateQuestionInput,
): Promise<Outcome<Question>> {
  const result = await questionsProvider.update(input);
  if (!result.ok) return result;   // AppError already mapped at the provider call
  return { ok: true, data: result.data };
}
```

`throw` is still correct for a genuinely unrecoverable/programmer-error case
(a bug you want a stack trace for in server logs and a generic failure page
for the user) — it's the *expected*, caller-handled failure case this rule
targets. See `ARCH-WEB-APP-ERR-UNKNOWN-01` for how an unknown failure still
gets logged with full cause server-side before being mapped to an explicit
`unexpected` outcome; throwing loses that log-then-map step, not just the
client-visible message.

## Revalidation

A mutating Server Action does not automatically update any already-rendered
Server Component — Next.js caches render output until told otherwise.

```rule
id: PLAT-WEB-NEXT-APP-REVALIDATE-01
statement: A Server Action that mutates data MUST call `revalidatePath`/`revalidateTag` for every path whose Server Component render depends on that data.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-APP-REVALIDATE-01 — a mutating Server Action that doesn't revalidate leaves the affected Server Component stale until a hard refresh.
```

```typescript
'use server';
export async function updateQuestion(
  input: UpdateQuestionInput,
): Promise<Outcome<Question>> {
  const result = await questionsProvider.update(input);
  if (!result.ok) return result;
  revalidatePath(`/questions/${input.id}`);
  revalidatePath('/questions');   // the list view also depends on this data
  return { ok: true, data: result.data };
}
```

Prefer `revalidateTag` over `revalidatePath` once two or more unrelated
routes depend on the same underlying data — tagging the fetch once at the
read site avoids having to enumerate every dependent path at every mutation
site.

## Route Handler vs. Server Action

Not a rule — a judgment call, decided per feature:

| Use a **Server Action** when | Use a **Route Handler** when |
|---|---|
| A form mutation is invoked from a Client Component | An endpoint is called by another service, not this app's own UI |
| The caller is this app's own React tree | The caller needs standard HTTP semantics (cache headers, a webhook, a non-Next.js client) |
| No need for a stable public URL | A stable URL is required (an API contract, a redirect target) |

Both terminate at the same layer boundary — `ARCH-WEB-APP`'s "Route
Handler/Server Action" — and both follow the same error-mapping and
revalidation rules above; the choice is about the calling convention, not
the internal logic.

## Testing

See `QG-WEB-TESTING` for the full pattern — call the Server Action directly
as an async function and assert on its `Outcome`, don't mount a form to
test it.
