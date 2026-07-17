---
id: QG-WEB-TESTING
type: guide
layer: quality-gates
platform: [web]
architecture: [all]
requires: [QG-TESTING, CORE-TESTING]
related: [PLAT-WEB-HTTP, PLAT-WEB-FORMS]
tags: [testing, vitest, react-testing-library, msw, server-actions, middleware, e2e]
---

# Web Testing

`QG-TESTING` states the cross-platform testing philosophy and previously
carried a single line for web: "Vitest + React Testing Library for
component tests; MSW for API mocking." This doc replaces that one-liner
with real detail for every web architecture (`architecture: [all]`), not
just `web-app` — the Vitest/RTL/MSW baseline itself doesn't differ between
`web-spa`, `web-content`, and `web-app`; what differs is *what* gets
tested at the Provider boundary, covered in the `web-app`-specific sections
below.

## Baseline

Vitest is the test runner; React Testing Library renders components and
queries them the way a user would (by role/label, not by implementation
detail) — this is `QG-TESTING`'s "test behaviour, not implementation"
principle applied to a component test specifically.

```typescript
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

describe('QuestionRow', () => {
  it('shows the delete button when the question is deletable', () => {
    render(<QuestionRow question={mockQuestion({ deletable: true })} />);

    expect(screen.getByRole('button', { name: 'Delete question' })).toBeInTheDocument();
  });
});
```

## Server Actions

```rule
id: QG-WEB-TESTING-SA-01
statement: A Server Action is tested by calling it directly as an async function and asserting on its `Outcome`-shaped return — not by mounting a form and simulating a DOM submit.
type: hard
scope: testing
enforced_by: [reviewer]
violation_message: Violates QG-WEB-TESTING-SA-01 — call the Server Action directly; a DOM-level submit test is slower and tests React's form handling, not the action's own logic.
```

```typescript
it('returns a validation error when tokens is empty', async () => {
  const result = await createFitbQuestion({ presentation: 'fitb', tokens: [] });

  expect(result.ok).toBe(false);
  if (!result.ok) expect(result.error.type).toBe('validation');
});
```

A Server Action is already an isolated async function — the DOM, React's
rendering, and `react-hook-form`'s own submit handling are all things
`QG-WEB-TESTING-SA-01` explicitly excludes from this test's scope, since
none of them are what the action's own logic is responsible for.

## MSW at the Provider boundary

```rule
id: QG-WEB-TESTING-MSW-01
statement: A Provider-boundary test (a Route Handler/Server Action calling the PLAT-WEB-HTTP executor) mocks at the network layer with MSW — not by mocking the executor's own methods.
type: hard
scope: testing
enforced_by: [reviewer]
violation_message: Violates QG-WEB-TESTING-MSW-01 — mirrors QG-TEST-MOCK-01 ("mock at architectural boundaries, not within a layer"); mock the network, not the executor.
```

```typescript
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  http.patch('*/questions/:id', () => HttpResponse.json({ id: '1', tokens: ['a'] })),
);

it('maps a successful backend response to an Outcome', async () => {
  const result = await updateQuestion({ id: '1', tokens: ['a'] });

  expect(result).toEqual({ ok: true, data: expect.objectContaining({ id: '1' }) });
});
```

Mocking `questionsExecutor.patchJson` directly would test nothing about
whether the executor builds the right request or maps the right response —
it would only prove the calling code calls a mock the way the test told it
to. MSW intercepting at the actual network layer is what proves the
Server Action, the executor, and the error mapping all compose correctly
end to end, up to (but not including) a real backend.

A test that only needs a fake `HttpRequestExecutor` (not the real
`fetch`-based one) — a Server Action's own unit test, where the executor
itself is a collaborator to fake per `QG-TEST-SCOPE-01` — uses the fake
described in `PLAT-WEB-HTTP`'s testing section instead; MSW is specifically
for testing at the network boundary, not every test that happens to call a
Server Action.

## Middleware-gated auth

```rule
id: QG-WEB-TESTING-MW-01
statement: An auth flow gated by `middleware.ts` MUST be covered by an integration/E2E test — a component or unit test cannot exercise the middleware boundary.
type: soft
scope: testing
enforced_by: [reviewer]
violation_message: Violates QG-WEB-TESTING-MW-01 — middleware-gated auth needs an E2E layer (e.g. Playwright); no lower test level reaches it.
```

`middleware.ts` runs at the Next.js routing layer itself, before any
component renders — there is no way to mount a component or call a
function in a unit test that actually exercises it. An E2E test (Playwright
or equivalent) that navigates to a protected route as an unauthenticated
user and asserts on the redirect is the only test level that reaches this
boundary at all.

## What not to test

Same exclusions `QG-TESTING` already states, applied here: don't test
`react-hook-form`'s own internal state, don't test that Next.js itself
performs a redirect (that's framework behavior, not this app's logic), and
don't mock MSW's own request matching — if the MSW handler isn't matching,
that's a test bug to fix, not a case to work around with a broader mock.
