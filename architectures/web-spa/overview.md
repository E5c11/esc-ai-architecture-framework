---
id: ARCH-WEB
type: overview
layer: architectures
platform: [web]
architecture: web-spa
requires: [CORE-COUPLING, CORE-NAMING, PAT-DATA-ACCESS]
related: [ARCH-WEB-COMPONENTS, PLAT-WEB-REACT, PLAT-WEB-STATE, PLAT-WEB-FIREBASE]
tags: [web, react, spa, architecture, folder-structure, feature-folders]
---

# Web SPA Architecture

## What it is

Web SPA is a client-side single-page application architecture for React + TypeScript
projects. It covers two project variants that share the same architectural decisions:

- **Static website** — marketing / landing pages; no auth; content-driven
- **Firebase dashboard** — data-driven app with Firestore real-time data, auth, and routing

Both variants use the same component patterns, styling system, and folder layout.
Dashboard-specific concerns (Firebase data hooks, AuthContext, AuthGuard) are
additive — they build on the static website foundation.

## Folder structure

### Static website

```
src/
├── main.tsx
├── App.tsx
├── index.css              Global resets + media queries only
├── styles/
│   ├── theme.ts           Brand tokens and semantic colour aliases
│   └── commonStyles.ts    Shared React.CSSProperties objects
├── components/            Shared presentational UI primitives
├── content/
│   └── strings.ts         All user-visible text in one file
└── features/
    ├── home/              One folder per page / domain
    └── about/
```

### Firebase dashboard (extends website structure)

```
src/
├── ...                    Same foundation as website
├── common/                Shared utility components (ErrorBoundary, LoadingSpinner)
├── hooks/                 Custom data-fetching hooks
├── types/
│   └── firestore.ts       All Firestore document types
├── utils/
├── firebase/
│   └── firebaseConfig.ts  Firebase app init + exports
├── auth/
│   ├── LoginScreen.tsx
│   └── AuthGuard.tsx
├── layout/
│   ├── AppShell.tsx
│   ├── TopBar.tsx
│   └── Sidebar.tsx
└── features/
    └── [feature]/
        ├── FeaturePage.tsx    Container — data, loading, error
        └── FeatureTable.tsx   Presentation — render only
```

## Organise by domain, not by file type

```rule
id: ARCH-WEB-ORG-01
statement: Source files MUST be grouped by domain/feature, not by file type.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-ORG-01 — Source files MUST be grouped by domain/feature, not by file type.
```

`features/users/` (correct) vs `containers/`, `presentational/`, `pages/` as separate sibling directories (wrong).

Exception: `components/` (shared UI primitives), `hooks/` (shared data hooks),
`utils/` (shared utilities), and `types/` (shared type definitions) are legitimate
cross-feature directories because their contents are genuinely cross-cutting.

```rule
id: ARCH-WEB-ORG-02
statement: A component SHOULD live in the feature directory of its primary consumer.
type: soft
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-ORG-02 — A component SHOULD live in the feature directory of its primary consumer.
```

Only move it to `src/components/` when it is used in two or more distinct features. Do not pre-emptively abstract.

## Layer responsibilities

| Layer | Directory | Responsibility |
|---|---|---|
| Routing | `App.tsx` | Route declarations, layout wrappers, auth guards |
| Layout | `layout/` | App shell, navigation chrome (dashboard only) |
| Feature | `features/[name]/` | Container + presentation components for one domain |
| Shared UI | `components/` | Pure presentational primitives used across features |
| Data | `hooks/` | Custom hooks — all Firebase/API calls |
| Types | `types/` | TypeScript interfaces for external data shapes |
| Styles | `styles/` | Theme tokens and shared style objects |
| Content | `content/` | User-visible text strings |

## Dependency direction

```
App.tsx
  └── features/  → components/, hooks/, types/, styles/
      └── hooks/ → firebase/
```

Features depend on shared layers; shared layers do not depend on features.
Hooks contain all external data access; components never call Firebase directly.

```rule
id: ARCH-WEB-DEP-01
statement: Components MUST NOT make direct Firebase or API calls.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-DEP-01 — Components MUST NOT make direct Firebase or API calls.
```

All data fetching lives in custom hooks in `src/hooks/`. Components call hooks; hooks call external services.

## Execution order for a new feature

1. Add type(s) to `src/types/firestore.ts` (dashboard) or `src/content/` (website)
2. Write the data hook in `src/hooks/` (dashboard)
3. Write the presentation component (`FeatureTable.tsx`)
4. Write the container component (`FeaturePage.tsx`) using the hook
5. Register the route in `App.tsx`
