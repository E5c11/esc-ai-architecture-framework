---
id: PLAT-WEB-DS-THEME
type: guide
layer: platforms
platform: [web]
architecture: [web-app, web-content]
requires: [CORE-COUPLING]
related: [PLAT-WEB-DS-COMPONENT, PLAT-WEB-DS-ICONS]
tags: [design-system, theme, tailwind, tokens, colors, spacing, typography, dark-mode]
---

# Design System — Theme System

Mirrors `platforms/mobile/design-system/theme.md`'s structure, restated for
Tailwind/React. Shared by `web-app` and `web-content` — both use Tailwind
and neither architecture's layering decisions constrain what a design token
is.

## Core principle

**Never hardcode a design value in a component.** Every color, spacing,
radius, and type-scale value a component uses comes from a token defined in
`tailwind.config.ts`.

```rule
id: PLAT-WEB-DS-THEME-01
statement: Components MUST use Tailwind utility classes backed by tokens defined in `tailwind.config.ts` — no arbitrary-value classes (`bg-[#hex]`, `p-[Npx]`, `text-[Npx]`) for any value a token already covers.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DS-THEME-01 — use a `tailwind.config.ts` token, not an arbitrary-value class.
```

This is what makes a Tailwind project's `PLAT-WEB-STYLING`-equivalent
discipline enforceable — `PLAT-WEB-STYLING`'s own token rule
(`PLAT-WEB-STYLE-TOKEN-01`/`02`) governs the inline-`CSSProperties` default
for `web-spa`; this rule is the Tailwind-specific restatement for a project
that has adopted it, and stays a distinct rule owned by this doc rather than
edited into `PLAT-WEB-STYLING` (which still governs `web-spa` unchanged).

```typescript
// tailwind.config.ts
export default {
  theme: {
    extend: {
      colors: {
        primary:    { DEFAULT: '#5C6B2E', hover: '#4a5624' },
        surface:    '#302E2C',
        background: '#1C1008',
        error:      '#D32F2F',
      },
      spacing: {
        xs: '4px', sm: '8px', md: '16px', lg: '24px', xl: '32px',
      },
      borderRadius: {
        sm: '4px', md: '8px', lg: '12px', xl: '16px',
      },
      fontSize: {
        'title-lg': ['28px', { lineHeight: '36px', fontWeight: '700' }],
        'title-md': ['20px', { lineHeight: '28px', fontWeight: '600' }],
        'body':     ['16px', { lineHeight: '24px' }],
        'label':    ['14px', { lineHeight: '20px', fontWeight: '500' }],
      },
    },
  },
};
```

```tsx
// ❌ Wrong — arbitrary values bypass the token system entirely
<div className="bg-[#5C6B2E] p-[16px] rounded-[8px] text-[20px]">

// ✅ Correct — every value resolves to a config token
<div className="bg-primary p-md rounded-md text-title-md">
```

## Promoting a value to a token

```rule
id: PLAT-WEB-DS-THEME-02
statement: A value used in 3+ places, or specified by a design spec, MUST be added to `tailwind.config.ts` as a token — not repeated as an arbitrary-value class each time.
type: soft
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DS-THEME-02 — promote a repeated value to a token instead of repeating an arbitrary-value class.
```

This is the rule that turns a Tailwind adoption into an actual enforced
convention rather than a per-project exception layered on top of
`PLAT-WEB-STYLING`'s inline-`CSSProperties` default — the same threshold
`DS-THEME-10` uses for mobile's theme files, restated for
`tailwind.config.ts`.

## Dark mode

Tailwind's class strategy (`darkMode: 'class'`) toggles dark-mode styles by
adding a `dark` class to a root element (typically `<html>`), rather than
relying on `prefers-color-scheme` alone — this lets an app offer a manual
theme toggle in addition to (or instead of) following the OS setting.

```typescript
// tailwind.config.ts
export default {
  darkMode: 'class',
  // ...
};
```

```tsx
<div className="bg-background text-white dark:bg-white dark:text-background">
```

Token names stay semantic (`bg-surface`, not `bg-gray-900`) so a component
never needs a separate `dark:` variant for a value the token itself should
resolve — reach for `dark:` only when light and dark mode genuinely need
different tokens, not as the default way to theme every value.
