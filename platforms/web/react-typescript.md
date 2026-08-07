---
id: PLAT-WEB-REACT
type: guide
layer: platforms
platform: [web]
architecture: web-spa
requires: [ARCH-WEB, ARCH-WEB-COMPONENTS]
related: [PLAT-WEB-STYLING, PLAT-WEB-STATE, PLAT-WEB-FIREBASE]
tags: [react, typescript, strict, props, hooks, cleanup, as-const]
status: active
---

# React + TypeScript Platform Guide

Extends: `ARCH-WEB`, `ARCH-WEB-COMPONENTS`

## TypeScript config

```json
{
  "compilerOptions": {
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

```rule
id: PLAT-WEB-TS-STRICT-01
statement: TypeScript MUST run with `strict: true`, `noUnusedLocals: true`, and `noUnusedParameters: true`.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-TS-STRICT-01 — TypeScript MUST run with `strict: true`, `noUnusedLocals: true`, and `noUnusedParameters: true`.
```

The build MUST pass `tsc -b` with zero errors before every deploy.

```rule
id: PLAT-WEB-TS-ANY-01
statement: `any` is forbidden.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-TS-ANY-01 — `any` is forbidden.
```

Use `unknown` at genuine unknown boundaries and narrow it. If a third-party library forces `any`, isolate it behind a typed wrapper function and annotate the wrapper with an explicit type.

## Props interfaces

```rule
id: PLAT-WEB-TS-PROPS-01
statement: Every component MUST declare an explicit props interface.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-TS-PROPS-01 — Every component MUST declare an explicit props interface.
```

Never rely on implicit prop inference.

```typescript
// ✅
interface CardProps {
  title: string;
  onPress: () => void;
}
const Card: React.FC<CardProps> = ({ title, onPress }) => ...

// ✗ — no explicit type, inferred from usage
const Card = ({ title, onPress }) => ...
```

```rule
id: PLAT-WEB-TS-PROPS-02
statement: Props interfaces SHOULD be defined inline at the top of the component file.
type: soft
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-TS-PROPS-02 — Props interfaces SHOULD be defined inline at the top of the component file.
```

Only extract to a shared `.ts` file when the exact same interface is imported by two or more components.

## Type declarations

```rule
id: PLAT-WEB-TS-TYPES-01
statement: Prefer `interface` over `type` for object shapes.
type: soft
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-TS-TYPES-01 — Prefer `interface` over `type` for object shapes.
```

Use `type` for unions, mapped types, and utility types.

```rule
id: PLAT-WEB-TS-CONST-01
statement: Route constants and enum-like values SHOULD use `as const`:
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-TS-CONST-01 — Route constants and enum-like values SHOULD use `as const`:
```

```typescript
export const ROUTES = {
  HOME:    '/',
  USERS:   '/users',
  CONTENT: '/content',
} as const;
```

## Hook return types

```rule
id: PLAT-WEB-TS-HOOKS-01
statement: Data-fetching hooks MUST declare an explicit return type.
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-TS-HOOKS-01 — Data-fetching hooks MUST declare an explicit return type.
```

The standard shape for Firestore/async data hooks is:

```typescript
{ data: T[]; loading: boolean; error: string | null }
```

Never let TypeScript infer the hook return type — it makes the shape implicit
and harder to enforce from callers.

## useEffect cleanup

```rule
id: PLAT-WEB-TS-CLEANUP-01
statement: Every `useEffect` that starts a subscription or listener MUST return the cleanup/unsubscribe function.
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-TS-CLEANUP-01 — Every `useEffect` that starts a subscription or listener MUST return the cleanup/unsubscribe function.
```

Failing to return cleanup causes memory leaks and stale listeners after the component unmounts.

```typescript
useEffect(() => {
  const unsub = onSnapshot(q, handler);
  return unsub;  // ✅ always return
}, []);

// ✗ — subscription never cleaned up
useEffect(() => {
  onSnapshot(q, handler);
}, []);
```

## Firestore type casting

Firestore returns `DocumentData` (untyped). Cast explicitly when mapping documents:

```typescript
snap.docs.map(d => ({ id: d.id, ...d.data() } as UserDoc))
```

```rule
id: PLAT-WEB-TS-FIRESTORE-01
statement: All Firestore document interfaces MUST be declared in `src/types/firestore.ts`.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-TS-FIRESTORE-01 — All Firestore document interfaces MUST be declared in `src/types/firestore.ts`.
```

Never define document types inline inside a hook or component file. This makes the Firestore schema discoverable and consistent across the codebase.

## Anonymous components

```rule
id: PLAT-WEB-REACT-ANON-01
statement: Avoid inline anonymous components in JSX.
type: soft
scope: naming
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-REACT-ANON-01 — Avoid inline anonymous components in JSX.
```

If a sub-component becomes complex, extract it to a named constant or its own file. Anonymous components defeat React's reconciliation — they remount on every parent render instead of diffing.
