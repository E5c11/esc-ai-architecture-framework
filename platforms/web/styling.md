---
id: PLAT-WEB-STYLING
type: guide
layer: platforms
platform: [web]
architecture: web-spa
requires: [ARCH-WEB]
related: [PLAT-WEB-REACT, PLAT-WEB-A11Y]
tags: [styling, css-properties, theme, design-tokens, inline-styles, common-styles]
---

# Styling System

Extends: `ARCH-WEB`

## Approach

All styling uses inline `React.CSSProperties` objects as the primary method.
No CSS-in-JS libraries, no Tailwind, no CSS Modules — unless the project was
explicitly started with one of those tools.

The system has three layers. Apply them in order and never skip a layer.

## Layer 1: `src/styles/theme.ts` — Design tokens

Define raw brand values first. Export only semantic aliases. Components MUST
import from the semantic aliases, never from the raw values.

```typescript
// Raw values — private
const Cream      = '#F2F1C7';
const OliveGreen = '#5C6B2E';
const Stone      = '#8C8574';

// Semantic aliases — these are the public exports
export const colors = {
  primary:        OliveGreen,
  background:     Cream,
  textMuted:      Stone,

  // Dashboard surface hierarchy
  bgPage:         '#1C1008',
  bgSurface:      '#2C1E10',
  bgCard:         '#302E2C',
  textPrimary:    '#F5F0E8',
  textSecondary:  '#D0CCC4',
  actionPrimary:  OliveGreen,
  actionHover:    '#4a5624',
  error:          '#D32F2F',
};

export const spacing = { xs: 4, sm: 8, md: 16, lg: 24, xl: 32 };
export const radius  = { sm: 4, md: 8, lg: 12, xl: 16 };
```

```rule
id: PLAT-WEB-STYLE-TOKEN-01
statement: Components MUST import colour values from semantic aliases (`colors.textPrimary`) — never raw hex values (`'#F5F0E8'`).
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-STYLE-TOKEN-01 — Components MUST import colour values from semantic aliases (`colors.textPrimary`) — never raw hex values (`'#F5F0E8'`).
```

Raw values scattered across component files make theme changes require a global search.

```rule
id: PLAT-WEB-STYLE-TOKEN-02
statement: Spacing and border-radius values MUST use the tokens from `theme.ts`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-STYLE-TOKEN-02 — Spacing and border-radius values MUST use the tokens from `theme.ts`.
```

No magic numbers. If a required value is not in the theme, add it there first.

## Layer 2: `src/styles/commonStyles.ts` — Shared style objects

Reusable `React.CSSProperties` objects that appear across multiple components.

```typescript
import type React from 'react';
import { colors, spacing, radius } from './theme';

export const card: React.CSSProperties = {
  backgroundColor: colors.bgCard,
  borderRadius: radius.lg,
  padding: spacing.lg,
  border: '1px solid rgba(255,255,255,0.06)',
};

export const pageContainer: React.CSSProperties = {
  backgroundColor: colors.bgPage,
  minHeight: '100vh',
  color: colors.textPrimary,
};

export const primaryButton: React.CSSProperties = {
  backgroundColor: colors.actionPrimary,
  color: '#fff',
  border: 'none',
  borderRadius: radius.md,
  padding: `${spacing.sm}px ${spacing.md}px`,
  cursor: 'pointer',
  fontWeight: 600,
};
```

```rule
id: PLAT-WEB-STYLE-COMMON-01
statement: When the same style object appears in two or more component files, move it to `commonStyles.ts`.
type: soft
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-STYLE-COMMON-01 — When the same style object appears in two or more component files, move it to `commonStyles.ts`.
```

Do not duplicate style objects across files.

```rule
id: PLAT-WEB-STYLE-COMMON-02
statement: Extend shared styles using object spread:
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-STYLE-COMMON-02 — Extend shared styles using object spread:
```

```typescript
const containerStyle: React.CSSProperties = {
  ...card,             // extend from commonStyles
  flexDirection: 'column',
  gap: 12,
};
```

## Layer 3: Component-level styles

Component-scoped style constants. Defined after the component function, at the
bottom of the file, and not exported.

```typescript
// components/UserCard.tsx

const UserCard: React.FC<UserCardProps> = ({ name }) => (
  <div style={wrapperStyle}>
    <span style={nameStyle}>{name}</span>
  </div>
);

export default UserCard;

// ↓ Style constants after the export
const wrapperStyle: React.CSSProperties = {
  ...card,
  display: 'flex',
  alignItems: 'center',
};

const nameStyle: React.CSSProperties = {
  fontSize: 15,
  fontWeight: 700,
  color: colors.textPrimary,
};
```

```rule
id: PLAT-WEB-STYLE-SCOPE-01
statement: Component style constants MUST be defined after the component function — never inside the function body.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-STYLE-SCOPE-01 — Component style constants MUST be defined after the component function — never inside the function body.
```

Constants inside the function body are recreated on every render, defeating object identity and causing avoidable re-renders.

```rule
id: PLAT-WEB-STYLE-SCOPE-02
statement: Component-scoped styles SHOULD NOT be exported.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-STYLE-SCOPE-02 — Component-scoped styles SHOULD NOT be exported.
```

If a style needs to be shared, it belongs in `commonStyles.ts`.

## CSS classes (`index.css`)

Use CSS classes only for things `React.CSSProperties` cannot express:

- Global resets and body styles
- Layout shells that need media queries (`@media`)
- Pseudo-class states (`:hover`, `:focus`, `backdrop-filter`)

```css
/* index.css — resets and media queries only */
@media (min-width: 1024px) {
  .sidebar { display: flex; }
}
```

```rule
id: PLAT-WEB-STYLE-CSS-01
statement: CSS class files MUST NOT contain component visual styling (colours, typography, component-specific spacing).
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-STYLE-CSS-01 — CSS class files MUST NOT contain component visual styling (colours, typography, component-specific spacing).
```

Those belong in the three-layer TypeScript system. CSS classes are a last resort for things the inline system cannot express.

```rule
id: PLAT-WEB-STYLE-FOCUS-01
statement: Never remove the browser focus ring with `outline: none` without providing a replacement visible focus indicator.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-STYLE-FOCUS-01 — Never remove the browser focus ring with `outline: none` without providing a replacement visible focus indicator.
```

Removing the focus ring without a replacement breaks keyboard navigation.
