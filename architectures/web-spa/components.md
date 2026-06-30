---
id: ARCH-WEB-COMPONENTS
type: rules
layer: architectures
platform: [web]
architecture: web-spa
requires: [ARCH-WEB, CORE-COUPLING, CORE-DI]
related: [PLAT-WEB-REACT, PLAT-WEB-STATE, PLAT-WEB-A11Y]
tags: [components, container, presentation, error-boundary, state-guards, props, composition]
---

# Component Architecture

## Container / Presentation split

Any feature that fetches data uses a two-component structure:

**Container** (`FeaturePage.tsx`):
- Calls the data hook
- Owns loading and error state guards
- Renders nothing while data is loading or errored
- Passes data down to the presentation component as props
- Contains no styles

**Presentation** (`FeatureTable.tsx`, `FeatureCard.tsx`):
- Receives data via props
- Renders only — no data fetching, no Firebase calls
- Owns all the visual styles
- Is stateless or manages only local UI state (e.g. expanded/collapsed)

**Rule ARCH-WEB-CP-01 (hard):** Container components MUST guard all three states —
loading, error, and data — before rendering the presentation component. Never render
a presentation component with potentially undefined or in-flight data.

```tsx
const FeaturePage: React.FC = () => {
  const { data, loading, error } = useFeatureData();

  if (loading) return <LoadingSpinner />;
  if (error)   return <ErrorMessage message={error.message} />;

  return <FeatureTable rows={data} />;
};
```

**Rule ARCH-WEB-CP-02 (soft):** Container components SHOULD contain no visual styles.
The presentation component is the styling boundary.

## Error boundaries

A runtime error in any component, without a boundary, crashes the entire page.

**Rule ARCH-WEB-EB-01 (hard):** Every page-level route MUST be wrapped in an
`ErrorBoundary`. For dashboards, wrapping the `AppShell` (which renders inside
the layout) is sufficient; for websites, wrap each route element.

```tsx
// App.tsx — website
<Route path="/" element={<ErrorBoundary><Home /></ErrorBoundary>} />

// App.tsx — dashboard (wrapping the shell is enough)
<Route element={<ErrorBoundary><AppShell /></ErrorBoundary>}>
  <Route path="/" element={<OverviewPage />} />
  <Route path="/users" element={<UsersPage />} />
</Route>
```

`ErrorBoundary` must be a class component (React does not support error boundaries
as function components). Place it in `src/common/ErrorBoundary.tsx`.

## Props — Interface Segregation

**Rule ARCH-WEB-PROPS-01 (hard):** Props interfaces MUST contain only the fields
a component actually uses. Never pass an entire data object when the component
needs only one or two fields.

```tsx
// ✅ — component needs name and avatar only
<UserCard name={user.displayName} avatarUrl={user.photoURL} />

// ✗ — component now depends on the entire UserDoc shape
<UserCard user={user} />
```

Oversized props create invisible coupling: the component breaks whenever the
parent's data shape changes, even if the rendered output is unaffected.

**Rule ARCH-WEB-PROPS-02 (soft):** Props interfaces SHOULD be defined inline at the
top of the component file. Only extract to a shared type when the exact same
interface is imported by two or more components.

## Composition over conditional props

**Rule ARCH-WEB-COMP-01 (soft):** Shared components SHOULD express variation through
composition (`children`, slot props, wrapping) rather than through special-case
boolean or enum props. Conditional branches inside a component accumulate and
the component becomes unreadable.

```tsx
// ✅ — caller composes what it needs
<Card>
  <Card.Header>Title</Card.Header>
  <MetricValue value={42} />
</Card>

// ✗ — grows a new branch for every caller's special need
<Card showHeader variant="large" metricMode="compact" />
```

## Extracting shared components

**Rule ARCH-WEB-SHARE-01 (soft):** A component SHOULD only be moved to `src/components/`
when it is used in two or more features. Do not move it there pre-emptively. Premature
abstraction creates components with no consumers and diffuse responsibility.

## Naming

**Rule ARCH-WEB-NAME-01 (hard):** Component files MUST use PascalCase `.tsx`.
Hook files: `use` prefix, camelCase, `.ts`. Utility files: camelCase, `.ts`.
Type/interface files: PascalCase, `.ts`.

**Rule ARCH-WEB-NAME-02 (soft):** Components SHOULD be named by what they show,
not by their technical role. `UserTable` over `UserPresenter`. `OverviewPage`
over `OverviewContainer`.

## Export convention

**Rule ARCH-WEB-EXPORT-01 (soft):** Component files SHOULD use `export default`.
Named exports are for hooks, types, and utilities.

## Keeping page components lean

Static data arrays, content strings, and large static structures belong in
`src/content/`, not inlined in page component files. Sub-components larger than
approximately 30 lines belong in their own file in `src/components/` or the
feature folder.
