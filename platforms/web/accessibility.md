---
id: PLAT-WEB-A11Y
type: rules
layer: platforms
platform: [web]
architecture: web-spa
requires: [ARCH-WEB, ARCH-WEB-COMPONENTS]
related: [PLAT-WEB-REACT, PLAT-WEB-STYLING]
tags: [accessibility, a11y, semantic-html, aria, alt-text, headings, keyboard, focus]
---

# Accessibility

Extends: `ARCH-WEB`

Accessibility is not an optional polish step. It affects real users (screen readers,
keyboard navigation, low-vision users) and search engine indexing. The baseline rules
below are low-effort and must be the default, not an afterthought.

## Semantic HTML

```rule
id: PLAT-WEB-A11Y-SEMANTIC-01
statement: Use the HTML element that describes the content.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-A11Y-SEMANTIC-01 — Use the HTML element that describes the content.
```

The browser provides keyboard handling, focus management, and screen reader announcements automatically for semantic elements. `<div onClick>` provides none of that for free.

| Use | Not | For |
|---|---|---|
| `<button>` | `<div onClick>` | Clickable actions |
| `<a href>` | `<div onClick>` | Navigation links |
| `<nav>` | `<div>` | Navigation regions |
| `<main>` | `<div>` | Primary page content |
| `<h1>`–`<h6>` | `<p style="font-size: 24px">` | Headings |
| `<ul>` / `<ol>` + `<li>` | `<div>` | Lists |

## Images

```rule
id: PLAT-WEB-A11Y-ALT-01
statement: Every `<img>` MUST have an `alt` attribute.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-A11Y-ALT-01 — Every `<img>` MUST have an `alt` attribute.
```

Missing `alt` is a hard accessibility failure.

- Meaningful image: `alt="Description of what the image shows"`
- Decorative image: `alt=""` (empty string — tells screen readers to skip it)

```tsx
<img src="/hero.png" alt="Student studying with the app" />
<img src="/divider.png" alt="" />
```

## Icon-only interactive elements

```rule
id: PLAT-WEB-A11Y-ARIA-01
statement: Any interactive element with no visible text label MUST have `aria-label`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-A11Y-ARIA-01 — Any interactive element with no visible text label MUST have `aria-label`.
```

Without it, screen readers announce only the element type ("button") with no context.

```tsx
<button aria-label="Close menu">✕</button>

<a href={storeUrl} aria-label="Get it on Google Play">
  <img src="/google-play-badge.png" alt="" />
</a>
```

## Heading hierarchy

```rule
id: PLAT-WEB-A11Y-HEADING-01
statement: Each page MUST have exactly one `<h1>` (the page title).
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-A11Y-HEADING-01 — Each page MUST have exactly one `<h1>` (the page title).
```

Heading levels must not skip (`<h1>` → `<h3>` without an intervening `<h2>` is wrong). Use `<h2>` for sections, `<h3>` for sub-sections.

```tsx
<h1>Page Title</h1>
  <h2>Section One</h2>
    <h3>Sub-section</h3>
  <h2>Section Two</h2>
```

## Focus management

```rule
id: PLAT-WEB-A11Y-FOCUS-01
statement: Never remove the browser focus ring with `outline: none` without providing a visible replacement focus indicator.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-A11Y-FOCUS-01 — Never remove the browser focus ring with `outline: none` without providing a visible replacement focus indicator.
```

The focus ring is the only visible signal for keyboard users about which element is active. If the default ring clashes with the design, replace it with a custom `outline` or `box-shadow` — do not simply remove it.

## Loading and error guards

```rule
id: PLAT-WEB-A11Y-GUARD-01
statement: Containers MUST handle `loading` and `error` states before rendering data components.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-A11Y-GUARD-01 — Containers MUST handle `loading` and `error` states before rendering data components.
```

Rendering a component whose data may still be `undefined` causes both a visual flash and a potential crash.

```tsx
if (loading) return <LoadingSpinner />;
if (error)   return <ErrorMessage message={error} />;
return <DataTable rows={data} />;
```

See also `ARCH-WEB-COMPONENTS` rule ARCH-WEB-CP-01.

## Error boundaries

```rule
id: PLAT-WEB-A11Y-EB-01
statement: Every page-level route MUST be wrapped in an `ErrorBoundary`.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-A11Y-EB-01 — Every page-level route MUST be wrapped in an `ErrorBoundary`.
```

A runtime error in one component without a boundary crashes the entire page including the navigation. With a boundary, only the broken page shows an error; the rest of the app keeps working.

See `ARCH-WEB-COMPONENTS` for the `ErrorBoundary` implementation.
