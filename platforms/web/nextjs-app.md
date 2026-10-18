---
id: PLAT-WEB-NEXT-APP
type: guide
layer: platforms
platform: [web]
architecture: [web-app]
requires: [PLAT-WEB-NEXT, ARCH-WEB-APP, ARCH-WEB-APP-ERR-CLASSES]
related: [PLAT-WEB-HTTP, PLAT-WEB-NEXT-APP-DEPLOY, QG-WEB-TESTING]
tags: [nextjs, server-actions, route-handlers, revalidation, outcome, error-digest]
status: active
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

## Every action is an endpoint

Next.js registers each export of a `'use server'` file as a callable server reference, whether or not a
form uses it. A read helper or an update function exported from such a file is therefore reachable by
any HTTP client that has its action id; TypeScript types are not checked at run time. Observed on a real
app: an unauthenticated POST listed customer records and, through an unchecked `{ ...existing, ...patch }`,
overwrote a customer's name and a creation timestamp. This is the Server Action counterpart of
`PLAT-WEB-NEXT-FB-CALLABLE-01`.

```rule
id: PLAT-WEB-NEXT-APP-ACTION-01
statement: Every export of a `'use server'` file is a public endpoint: it MUST be a deliberate entry point and nothing else, MUST take its input as `unknown` and validate it with a schema that rejects unknown keys, and MUST check the caller's authority wherever the data is not public.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-APP-ACTION-01 — Every export of a `'use server'` file is a public endpoint: it MUST be a deliberate entry point and nothing else, MUST take its input as `unknown` and validate it with a schema that rejects unknown keys, and MUST check the caller's authority wherever the data is not public.
```

```typescript
// ❌ Wrong — exported, so callable; the patch is typed but never checked
'use server';
export async function updateFault(id: string, patch: UpdateFaultInput) {
  return store.update(id, { ...existing, ...patch });
}

// ✅ Correct — one entry point; the use case parses `unknown` with a strict schema
'use server';
export async function saveFaultTriage(id: string, _prev: FormState, formData: FormData): Promise<FormState> {
  return toFormState(await serverGraph().triageFault(id, pickFields(formData, TRIAGE_FIELDS)));
}
```

A form also carries fields the framework adds, so the action picks only the form's named fields before
the strict schema sees them. Put the schema in the use case, not only in the action, so that every entry
point (a Server Action today, a Route Handler later) gets the same checks (`PLAT-WEB-FORMS-SSOT-01`).
Reads for rendering are not actions: a Server Component calls the server DataSource or use case directly
(`PLAT-WEB-NEXT-DATA-FETCH-01`).

## Revalidation

A mutating Server Action does not automatically update any already-rendered
Server Component — Next.js caches render output until told otherwise.

```rule
id: PLAT-WEB-NEXT-APP-REVALIDATE-01
statement: A Server Action that mutates data MUST invalidate every cached result that depends on it: `updateTag` where the user must see their own change immediately, `revalidateTag(tag, profile)` where stale-while-revalidate is acceptable, and `revalidatePath` for a route that has no tag.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-APP-REVALIDATE-01 — a mutating Server Action that doesn't invalidate leaves the affected Server Component stale until a hard refresh.
```

```typescript
'use server';
import { updateTag, revalidateTag } from 'next/cache';
import { tags } from '@/features/questions/cacheTags';       // one module (PLAT-WEB-NEXT-DATA-TAG-01)

export async function updateQuestion(
  input: UpdateQuestionInput,
): Promise<Outcome<Question>> {
  const result = await questionsProvider.update(input);
  if (!result.ok) return result;
  updateTag(tags.question(input.id));          // read-your-writes: the editor sees the change now
  revalidateTag(tags.questionList, 'max');     // the list may be briefly stale
  return { ok: true, data: result.data };
}
```

Revalidation applies to cached results. A project that caches nothing (Cache Components, reads made
request-time and uncached) has nothing to invalidate, and a `revalidatePath` added out of habit only
hides that; removing every call from such an app left it correct on a production build.

Written for Next.js 16 (`PLAT-WEB-NEXT`): `revalidateTag` takes a second argument naming a
`cacheLife` profile and the one-argument form is deprecated; `updateTag` is for Server
Actions only and expires and refreshes the data within the same request; `refresh`
refreshes the client router from an action. Prefer tags over `revalidatePath` once two or
more unrelated routes depend on the same data: tagging once at the read site avoids
enumerating every dependent path at every mutation site. The tag names come from one
module (`PLAT-WEB-NEXT-DATA-TAG-01`).

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
