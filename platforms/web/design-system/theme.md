---
id: PLAT-WEB-DS-THEME
type: guide
layer: platforms
platform: [web]
architecture: [web-app, web-content]
requires: [CORE-COUPLING]
related: [PLAT-WEB-DS-COMPONENT, PLAT-WEB-DS-ICONS, PLAT-WEB-NEXT, PLAT-WEB-A11Y]
tags: [design-system, theme, tailwind, tailwind-v4, tokens, colors, spacing, typography, dark-mode, data-viz, charts, next-font]
status: active
---

# Design System: Theme System

Mirrors `platforms/mobile/design-system/theme.md`'s structure, restated for Tailwind
and React. Shared by `web-app` and `web-content`: both use Tailwind, and neither
architecture's layering decisions constrain what a design token is.

**Written for Tailwind CSS 4.x**, checked against the Tailwind documentation and the npm
registry on 2026-10-18 (4.3.3). Tailwind 4 is configured in CSS, not in
`tailwind.config.ts`: design tokens are theme variables declared with `@theme`. A project
on Tailwind 3 keeps its tokens in `tailwind.config.ts` and applies the same rules to that
file; the version is recorded with the other pinned versions (`PLAT-WEB-NEXT-VERSION-01`).

## Core principle

**Never hardcode a design value in a component.** Every colour, spacing, radius,
type-scale and chart-colour value a component uses comes from a token defined once, in
the project's theme stylesheet.

```rule
id: PLAT-WEB-DS-THEME-01
statement: Components MUST use Tailwind utility classes backed by tokens defined in the project's theme (the `@theme` block of its global stylesheet) — no arbitrary-value classes (`bg-[#hex]`, `p-[Npx]`, `text-[Npx]`) for any value a token already covers.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DS-THEME-01 — use a theme token, not an arbitrary-value class.
```

This is what makes a Tailwind project's `PLAT-WEB-STYLING`-equivalent discipline
enforceable. `PLAT-WEB-STYLING`'s own token rule (`PLAT-WEB-STYLE-TOKEN-01`/`02`) governs
the inline-`CSSProperties` default for `web-spa`; this rule is the Tailwind restatement for
a project that has adopted it, and stays a distinct rule owned by this document.

## Setup

```css
/* app/globals.css: the one stylesheet that owns the tokens */
@import "tailwindcss";

@custom-variant dark (&:where(.dark, .dark *));

@theme inline {
  --color-surface: var(--surface);
  --color-on-surface: var(--on-surface);
  /* … every semantic token, mapped to a variable that changes per theme */
}

:root  { --surface: oklch(0.99 0 0);  --on-surface: oklch(0.2 0 0); }
.dark  { --surface: oklch(0.2 0.01 60); --on-surface: oklch(0.95 0 0); }
```

```rule
id: PLAT-WEB-DS-THEME-SETUP-01
statement: A Tailwind 4 project MUST configure Tailwind in CSS (`@import "tailwindcss"` and an `@theme` block) through the `@tailwindcss/postcss` plugin, MUST keep all tokens in that one stylesheet, and MUST NOT keep a second source of tokens in a JavaScript config unless it is loaded explicitly with `@config` for a stated migration reason.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DS-THEME-SETUP-01 — A Tailwind 4 project MUST configure Tailwind in CSS (`@import "tailwindcss"` and an `@theme` block) through the `@tailwindcss/postcss` plugin, MUST keep all tokens in that one stylesheet, and MUST NOT keep a second source of tokens in a JavaScript config unless it is loaded explicitly with `@config` for a stated migration reason.
```

Tailwind 4 does not detect a JavaScript config automatically; a leftover
`tailwind.config.ts` that is no longer loaded looks authoritative and does nothing.

## Two layers of tokens

A theme variable in `@theme` creates a utility (`--color-surface` gives `bg-surface`,
`text-surface`, `border-surface`) and a CSS variable. There are two kinds of value:

- **Palette**: the raw colours the brand owns (`--palette-olive-600`). Referenced only
  inside the theme stylesheet.
- **Semantic tokens**: names for what a colour is *for* (`surface`, `on-surface`,
  `primary`, `danger`). Components use only these.

When a semantic token points at another variable that changes per theme, declare it with
`@theme inline` so the utility uses the variable's current value, not the value at the
place it was defined.

```rule
id: PLAT-WEB-DS-THEME-LAYER-01
statement: Components MUST use semantic token utilities (`bg-surface`, `text-on-surface`, `border-danger`) and MUST NOT use palette utilities (`bg-olive-600`, `text-gray-900`) or raw colour values; palette values are referenced only inside the theme stylesheet.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DS-THEME-LAYER-01 — Components MUST use semantic token utilities (`bg-surface`, `text-on-surface`, `border-danger`) and MUST NOT use palette utilities (`bg-olive-600`, `text-gray-900`) or raw colour values; palette values are referenced only inside the theme stylesheet.
```

```tsx
// ❌ Wrong — a palette colour: a dark theme needs a second class in every component
<div className="bg-gray-900 text-gray-100 dark:bg-white dark:text-gray-900">

// ✅ Correct — one semantic class; the theme decides what "surface" is
<div className="bg-surface text-on-surface">
```

Semantic names are what let a rebrand or a new theme be one edit to one stylesheet.

## Promoting a value to a token

```rule
id: PLAT-WEB-DS-THEME-02
statement: A value used in 3+ places, or specified by a design spec, MUST be added to the theme as a token — not repeated as an arbitrary-value class each time.
type: soft
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DS-THEME-02 — promote a repeated value to a token instead of repeating an arbitrary-value class.
```

The same threshold `DS-THEME-10` uses for mobile's theme files, restated for `@theme`.
Name the token for its role, not its value: `--spacing-gutter`, not `--spacing-16px`.

## Dark mode

Tailwind's default `dark` variant follows the operating system's
`prefers-color-scheme`. An app that offers a manual switch overrides it to a selector, so
`dark:` utilities apply whenever a `dark` class is present higher in the tree:

```css
@custom-variant dark (&:where(.dark, .dark *));
```

```rule
id: PLAT-WEB-DS-THEME-DARK-01
statement: A project with a manual theme switch MUST override the `dark` variant to a selector (a `dark` class or a data attribute on the root element), MUST define every semantic token for both themes, and MUST treat a component-level `dark:` utility as the exception, not the way themes are applied.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DS-THEME-DARK-01 — A project with a manual theme switch MUST override the `dark` variant to a selector (a `dark` class or a data attribute on the root element), MUST define every semantic token for both themes, and MUST treat a component-level `dark:` utility as the exception, not the way themes are applied.
```

If a semantic token resolves to the right value in each theme, a component never needs a
`dark:` variant for it. A `dark:` utility is for the case where light and dark genuinely
need different *structure* (a border in one, none in the other), not for repainting.

```rule
id: PLAT-WEB-DS-THEME-DARK-02
statement: The theme class MUST be applied before first paint by a small blocking script in `<head>`, `<html>` MUST carry `suppressHydrationWarning`, and the class MUST NOT be set in an effect after mount.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DS-THEME-DARK-02 — The theme class MUST be applied before first paint by a small blocking script in `<head>`, `<html>` MUST carry `suppressHydrationWarning`, and the class MUST NOT be set in an effect after mount.
```

```tsx
// app/layout.tsx (Server Component)
const themeScript = `
  try {
    var t = localStorage.theme;
    var dark = t === 'dark' || (t !== 'light' && matchMedia('(prefers-color-scheme: dark)').matches);
    document.documentElement.classList.toggle('dark', dark);
  } catch (e) {}
`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head><script dangerouslySetInnerHTML={{ __html: themeScript }} /></head>
      <body>{children}</body>
    </html>
  );
}
```

A theme chosen in an effect paints the wrong theme first and then flips: a flash of white
for a dark-mode user, on every load. The script runs before the body is painted, so the
first frame is already right. React sees the `class` the script changed and the server
HTML did not have, which is why `suppressHydrationWarning` is on `<html>` (and only there).
This follows Tailwind's own three-way approach: `localStorage.theme` set to `light` or
`dark` for an explicit choice, removed to follow the system.

```rule
id: PLAT-WEB-DS-THEME-SWITCH-01
statement: The theme preference MUST be stored in one place (`localStorage.theme`: `light`, `dark`, or absent for the system setting), read only by the head script and the toggle, and every storage access MUST tolerate failure (private mode, blocked storage).
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DS-THEME-SWITCH-01 — The theme preference MUST be stored in one place (`localStorage.theme`: `light`, `dark`, or absent for the system setting), read only by the head script and the toggle, and every storage access MUST tolerate failure (private mode, blocked storage).
```

```rule
id: PLAT-WEB-DS-THEME-CONTRAST-01
statement: Every text, icon and control colour MUST meet WCAG 2.x AA contrast against the surface it sits on, in both themes (4.5:1 for body text, 3:1 for large text and for interface components), and the pairs MUST be checked when a token is added or changed.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DS-THEME-CONTRAST-01 — Every text, icon and control colour MUST meet WCAG 2.x AA contrast against the surface it sits on, in both themes (4.5:1 for body text, 3:1 for large text and for interface components), and the pairs MUST be checked when a token is added or changed.
```

A dark theme is not an inverted light theme: a muted grey that passes on white can fail on a
dark surface. Check the pairs in each theme, not one and assume the other.

## Data-visualisation tokens

A dashboard's charts are most of its colour. They follow the same rules as the rest of
the interface: tokens, defined per theme, used by name.

```css
@theme inline {
  --color-chart-1: var(--chart-1);  /* … through --color-chart-8 */
  --color-good: var(--status-good);
  --color-warn: var(--status-warn);
  --color-bad:  var(--status-bad);
  --color-neutral: var(--status-neutral);
}
```

```rule
id: PLAT-WEB-DS-THEME-VIZ-01
statement: Chart colours MUST be tokens defined once per theme (a categorical series `chart-1…chart-N`, sequential and diverging scales, and status colours `good`, `warn`, `bad`, `neutral`), and chart code MUST read them from the theme and MUST NOT contain a colour literal.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DS-THEME-VIZ-01 — Chart colours MUST be tokens defined once per theme (a categorical series `chart-1…chart-N`, sequential and diverging scales, and status colours `good`, `warn`, `bad`, `neutral`), and chart code MUST read them from the theme and MUST NOT contain a colour literal.
```

An SVG chart can use the CSS variable directly (`fill="var(--color-chart-1)"`). A
canvas-based chart cannot, so it reads the resolved value with `getComputedStyle` and
re-reads it when the theme changes; the token is still the only source.

```rule
id: PLAT-WEB-DS-THEME-VIZ-02
statement: A chart MUST NOT carry meaning by colour alone: a status or category MUST also be identified by a label, icon, pattern or position, and the palette MUST remain distinguishable under common colour-vision deficiencies.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DS-THEME-VIZ-02 — A chart MUST NOT carry meaning by colour alone: a status or category MUST also be identified by a label, icon, pattern or position, and the palette MUST remain distinguishable under common colour-vision deficiencies.
```

```rule
id: PLAT-WEB-DS-THEME-VIZ-03
statement: A chart SHOULD show at most eight categorical series; beyond that, the smaller series SHOULD be grouped as "Other" or the chart split, rather than adding colours that cannot be told apart.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DS-THEME-VIZ-03 — A chart SHOULD show at most eight categorical series; beyond that, the smaller series SHOULD be grouped as "Other" or the chart split, rather than adding colours that cannot be told apart.
```

Red and green carry good and bad by convention, and are the pair most often confused. They
are not used alone for a figure that matters (`PLAT-WEB-DS-THEME-VIZ-02`).

## Typography

```rule
id: PLAT-WEB-DS-THEME-TYPE-01
statement: Fonts MUST be loaded with `next/font` and assigned to `--font-*` theme variables through `@theme inline`, the type scale MUST be `--text-*` tokens with their line heights, and a component MUST NOT name a font file, a font URL or a literal font size.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DS-THEME-TYPE-01 — Fonts MUST be loaded with `next/font` and assigned to `--font-*` theme variables through `@theme inline`, the type scale MUST be `--text-*` tokens with their line heights, and a component MUST NOT name a font file, a font URL or a literal font size.
```

```css
@theme inline {
  --font-sans: var(--font-inter);          /* --font-inter is set by next/font on <html> */
  --text-title-md: 1.25rem;
  --text-title-md--line-height: 1.75rem;
}
```

`next/font` self-hosts the font and avoids a layout shift; `@theme inline` is needed
because the variable `next/font` sets lives on `<html>`, not at the place the theme
declares it.

## Violations

- `bg-[#5C6B2E]`, `p-[16px]` or `text-[20px]` in a component
- `bg-gray-900 dark:bg-white` in a component instead of `bg-surface`
- A `tailwind.config.ts` that Tailwind 4 never loads, holding tokens nobody sees applied
- The theme class set in an effect, so a dark-mode user sees white first
- A muted text colour checked only on the light theme
- A hex colour in a chart component
- A status shown only as red or green
- A tenth chart series in a ninth shade of blue
- A font file named in a component
