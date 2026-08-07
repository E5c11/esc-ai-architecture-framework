---
id: PLAT-WEB-DS-ICONS
type: guide
layer: platforms
platform: [web]
architecture: [web-app, web-content]
requires: [CORE-COUPLING, PLAT-WEB-DS-THEME]
related: [PLAT-WEB-DS-COMPONENT]
tags: [design-system, icons, centralized-module, lucide-react, accessibility]
status: active
---

# Design System — Icons

Same shape as mobile's `AppIcons` singleton (`DS-ICON-01`), restated for
React: one centralized module every component imports icons through, rather
than each component reaching into the icon library directly.

```rule
id: PLAT-WEB-DS-ICON-01
statement: Icons MUST be imported through a single centralized module — never imported ad hoc per-component directly from the icon library.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DS-ICON-01 — import icons through the centralized module, not ad hoc per-component.
```

```typescript
// components/ui/icons.ts
export {
  Trash as TrashIcon,
  Pencil as EditIcon,
  ArrowLeft as BackIcon,
  ArrowRight as ForwardIcon,
} from 'lucide-react';
```

```tsx
// ❌ Wrong — bypasses the centralized module
import { Trash } from 'lucide-react';

// ✅ Correct
import { TrashIcon } from '@/components/ui/icons';
```

A centralized module gives the same guarantees `AppIcons` gives mobile: one
place to swap the underlying icon library, one place to see every icon the
app actually uses, and a re-export name that stays stable even if the
underlying library's own export name changes.

## Icon library choice

`lucide-react` is a common default — tree-shakeable, one icon per import,
no wrapper component required — but the specific library is a project
decision, not dictated by this doc. Whatever library a project chooses, the
centralized re-export module above is what `PLAT-WEB-DS-ICON-01` requires;
the library itself is not a rule.

## Sizing and accessibility

Icon sizing follows the same token discipline `PLAT-WEB-DS-THEME` requires
for every other design value — a `size` prop resolves to a token, not a
literal pixel count:

```tsx
<TrashIcon className="size-icon-md" aria-hidden="true" />

<button aria-label="Delete question">
  <TrashIcon className="size-icon-md" aria-hidden="true" />
</button>
```

An icon inside a labeled interactive element (a `<button aria-label="...">`)
gets `aria-hidden="true"` — the label already carries the accessible name,
so the icon itself would otherwise be announced redundantly. A standalone
informative icon (not inside a labeled control) needs its own accessible
name instead — see `PLAT-WEB-A11Y-ARIA-01`.
