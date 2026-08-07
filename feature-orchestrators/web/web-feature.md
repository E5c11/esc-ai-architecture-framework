---
id: ORCH-WEB-FEAT
type: orchestrator
layer: feature-orchestrators
platform: [web]
architecture: [web-spa]
goal: "Implement a complete web feature page with data fetching, container/presentation split, and accessibility"
requires:
  - CORE-COUPLING
  - CORE-NAMING
  - CORE-TESTING
  - ARCH-WEB
  - ARCH-WEB-COMPONENTS
  - PLAT-WEB-REACT
  - PLAT-WEB-STYLING
  - PLAT-WEB-STATE
  - PLAT-WEB-FIREBASE
  - PLAT-WEB-A11Y
  - QG-TESTING
related: [QG-REVIEW]
tags: [web, feature, react, typescript, firebase, dashboard]
status: active
---

# Implement Web Feature (Web SPA)

## Goal

Produce a complete, accessible, typed feature page with a data hook, a container
component, and one or more presentation components.

## Before you start

Read all documents listed in `requires`. Decide upfront whether this feature
fetches live data (use `onSnapshot` hook) or static content (no hook needed).

---

## Phase 1 — Types

**Goal:** Firestore document types are defined before any hook or component is written.

Read: `PLAT-WEB-REACT`, `PLAT-WEB-FIREBASE`

### Steps (dashboard — data feature)

1. Add an interface for each Firestore collection the feature reads from, in
   `src/types/firestore.ts`:
   ```typescript
   export interface {Domain}Doc {
     id: string;
     // ... fields matching Firestore document shape
   }
   ```
2. All field types are explicit — no `any`, no `object`

### Steps (website — static content feature)

1. Add content strings to `src/content/strings.ts` or a dedicated
   `src/content/{feature}Content.ts`
2. Define TypeScript interfaces for structured static data

### Validation

- [ ] No inline document types in hooks or components
- [ ] No `any` types
- [ ] `tsc --noEmit` passes

---

## Phase 2 — Data hook (dashboard features only)

**Goal:** Live data is encapsulated in a hook that returns `{ data, loading, error }`.

Read: `PLAT-WEB-STATE`, `PLAT-WEB-FIREBASE`

### Steps

1. Create `src/hooks/use{Feature}.ts`
2. Hook returns `{ {feature}s: {Domain}Doc[]; loading: boolean; error: string | null }`
3. Use `onSnapshot` (not `getDocs`) for live data
4. Return the `onSnapshot` unsubscribe function from `useEffect`
5. Handle both the data callback and the error callback of `onSnapshot`

```typescript
export const use{Feature} = (): {
  {feature}s: {Domain}Doc[];
  loading: boolean;
  error: string | null;
} => {
  const [{feature}s, set{Feature}s] = useState<{Domain}Doc[]>([]);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState<string | null>(null);

  useEffect(() => {
    const q = query(collection(firestore, '{collection}'), orderBy('createdAt', 'desc'));
    const unsub = onSnapshot(
      q,
      snap => {
        set{Feature}s(snap.docs.map(d => ({ id: d.id, ...d.data() } as {Domain}Doc)));
        setLoading(false);
      },
      err => { setError(err.message); setLoading(false); },
    );
    return unsub;
  }, []);

  return { {feature}s, loading, error };
};
```

### Validation

- [ ] Hook returns exactly `{ data, loading, error }` shape (or named equivalent)
- [ ] `onSnapshot` subscription returned from `useEffect` for cleanup
- [ ] Error callback sets `error` state
- [ ] No Firestore calls outside `src/hooks/`

---

## Phase 3 — Presentation component(s)

**Goal:** Pure display component with all styles; no data fetching.

Read: `ARCH-WEB-COMPONENTS`, `PLAT-WEB-STYLING`, `PLAT-WEB-A11Y`

### Steps

1. Create `src/features/{feature}/{Feature}Table.tsx` (or `Card`, `List`, etc.)
2. Define props interface inline at the top — include only fields the component uses
3. Render using semantic HTML elements (`<table>`, `<ul>`, `<main>`, etc.)
4. Add `alt` to all `<img>` elements; add `aria-label` to icon-only interactive elements
5. Define style constants at the bottom of the file using the three-layer system:
   - Import from `colors`, `spacing`, `radius` in `theme.ts`
   - Extend from `commonStyles.ts` using spread where applicable
   - Component-specific styles as `const xyzStyle: React.CSSProperties = { ... }`

### Validation

- [ ] No data fetching, no Firebase calls, no hooks (other than local UI state) in this component
- [ ] All props explicitly typed in an inline interface
- [ ] No raw hex values — uses `colors.*` tokens
- [ ] Style constants defined after the component function, not inside it
- [ ] Semantic HTML: `<button>` not `<div onClick>`, `<a href>` not `<div onClick>`
- [ ] All `<img>` have `alt`; all icon-only buttons/links have `aria-label`

---

## Phase 4 — Container component

**Goal:** Container composes hook + guards + presentation; registers route.

Read: `ARCH-WEB-COMPONENTS`, `PLAT-WEB-STATE`

### Steps

1. Create `src/features/{feature}/{Feature}Page.tsx`
2. Call the data hook; guard all three states before rendering:
   ```typescript
   const { {feature}s, loading, error } = use{Feature}();
   if (loading) return <LoadingSpinner />;
   if (error)   return <ErrorMessage message={error} />;
   return <{Feature}Table rows={{feature}s} />;
   ```
3. Register the route in `App.tsx` wrapped in `<ErrorBoundary>`:
   ```tsx
   <Route path="/{feature}" element={<ErrorBoundary><{Feature}Page /></ErrorBoundary>} />
   ```
4. Add the route to `AppShell` sidebar / navigation if this is a dashboard feature
5. Update `sitemap.xml` if this is a public-facing website page

### Validation

- [ ] Container handles `loading`, `error`, and data — in that order — before rendering
- [ ] No inline styles on the container component
- [ ] Route wrapped in `<ErrorBoundary>`
- [ ] Route registered in `App.tsx`

---

## Phase 5 — Accessibility audit

**Goal:** Feature passes baseline accessibility requirements.

Read: `PLAT-WEB-A11Y`

### Checklist

- [ ] One `<h1>` on the page; section headings use `<h2>` / `<h3>` — no skipped levels
- [ ] All `<img>` have `alt` (empty string for decorative images)
- [ ] All icon-only buttons/links have `aria-label`
- [ ] Tab through all interactive elements in the browser — every element is reachable
  and has a visible focus indicator
- [ ] Screen reader can navigate the page meaningfully (optionally verify with VoiceOver/NVDA)

---

## Phase 6 — TypeScript and build gate

**Goal:** Build passes with zero type errors.

### Steps

1. Run `npm run build` — fix all TypeScript errors before proceeding
2. Check for `any` usages: `grep -r ": any" src/` should return nothing
3. Run `npm run preview` and navigate the new feature manually

### Validation

- [ ] `tsc -b` passes with zero errors
- [ ] No `any` types
- [ ] Feature works correctly in the browser preview
- [ ] No console errors in the browser developer tools
