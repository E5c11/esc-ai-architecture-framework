---
id: PLAT-WEB-DS-COMPONENT
type: guide
layer: platforms
platform: [web]
architecture: [web-app, web-content]
requires: [CORE-COUPLING, PLAT-WEB-DS-THEME]
related: [PLAT-WEB-DS-ICONS, PLAT-WEB-NEXT]
tags: [design-system, component, shared-components, server-components, client-components, tailwind]
---

# Design System — Shared Components

## Shared component location

```rule
id: PLAT-WEB-DS-COMPONENT-01
statement: A component used by two or more features MUST move to the shared `components/ui/` directory — never be duplicated across feature-local component files.
type: soft
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DS-COMPONENT-01 — promote a component used by 2+ features to `components/ui/` instead of duplicating it.
```

This mirrors `ARCH-WEB-CONTENT-SHARED-01`'s co-locate-until-reused
threshold — already governing content-object promotion for `web-content` —
restated here for components instead of content. The reuse threshold is the
same for the same reason: co-location is the right default until a second
consumer actually appears, at which point duplication (not premature
sharing) becomes the risk.

```
components/
└── ui/
    ├── Button.tsx
    ├── Card.tsx
    └── Input.tsx
features/
└── questions/
    └── components/
        └── QuestionRow.tsx   # feature-local until a second feature needs it
```

## Server-vs-Client default

A component in `components/ui/` follows the same default `PLAT-WEB-NEXT`
establishes for any component under `app/`: a Server Component unless it
itself needs browser-only APIs, local state, or event handlers. A shared
`Button` that only renders markup and forwards an `onClick` prop stays a
Server Component — passing a function as a prop from a Server Component
into a Client Component's `onClick` is fine; what pulls a component itself
across the boundary is using `useState`, `useEffect`, or a browser API
inside its own body. See `PLAT-WEB-NEXT-CLIENT-01`; this doc does not
re-derive that rule, only applies it to shared components specifically.

## Component signature convention

```tsx
interface ButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
  onClick?: () => void;
  className?: string;
}

export function Button({ children, variant = 'primary', disabled = false, onClick, className }: ButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'rounded-md px-md py-sm text-label',
        variant === 'primary'   && 'bg-primary text-white hover:bg-primary-hover',
        variant === 'secondary' && 'bg-surface text-white',
        disabled && 'opacity-38 pointer-events-none',
        className,
      )}
    >
      {children}
    </button>
  );
}
```

Props default to theme tokens, not raw values (`variant` selects a token
combination, not a literal color) — the same "customization defaults to
theme values" discipline `DS-THEME-07` states for mobile, restated here
implicitly through `PLAT-WEB-DS-THEME`'s token rules: nothing about this
component's own props reintroduces a raw hex or pixel value.

A `className` escape hatch is conventional (composed last via a `cn()`
helper so caller overrides win) but should stay an escape hatch, not the
primary way callers style the component — reach for a new `variant` before
reaching for an ad hoc `className` override that fights the component's own
default styling.

## Accessibility

```tsx
<button
  onClick={onDelete}
  aria-label="Delete question"      // PLAT-WEB-A11Y-ARIA-01 — icon-only, no visible label
>
  <TrashIcon />
</button>
```

Shared components are the highest-leverage place to get this right — an
accessibility fix inside `components/ui/Button.tsx` benefits every feature
using it, unlike a fix applied to one feature-local component.
