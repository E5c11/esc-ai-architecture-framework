---
id: PLAT-MOB-DS-THEME
type: guide
layer: platform
platform: [mobile]
architecture: [all]
requires: [PLAT-MOB-COMPOSE]
related: [PLAT-MOB-DS-COMPONENT, PLAT-MOB-DS-ICONS]
tags: [design-system, theme, material3, colors, typography, spacing, dimensions, compose]
status: active
---

# Design System — Theme System

## Core Principle

**Never hardcode theme values.** Always use theme accessors and dimension constants.

The theme system is built on Material 3 and provides:
- **Colors:** Brand colors mapped to M3 semantic color roles
- **Typography:** M3 type scale
- **Spacing:** 8-point grid system
- **Dimensions:** Component sizes, elevations, corners

---

## Colors

### Decision table

| Need | Use |
|------|-----|
| Primary action / CTA | `MaterialTheme.colorScheme.primary` |
| Text on primary | `MaterialTheme.colorScheme.onPrimary` |
| Card / dialog background | `MaterialTheme.colorScheme.surface` |
| Text on card | `MaterialTheme.colorScheme.onSurface` |
| Screen background | `MaterialTheme.colorScheme.background` |
| Selected state | `MaterialTheme.colorScheme.primaryContainer` |
| Error text / icon | `MaterialTheme.colorScheme.error` |
| Border / divider | `MaterialTheme.colorScheme.outline` |
| Disabled element | `MaterialTheme.colorScheme.onSurface.copy(alpha = Alpha.disabled)` |

```rule
id: DS-THEME-01
statement: Use `MaterialTheme.colorScheme` for all color access.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates DS-THEME-01 — Use `MaterialTheme.colorScheme` for all color access.
```

Never hardcode hex or `Color(0xFF...)` literals in components.

```rule
id: DS-THEME-02
statement: Brand-specific colors that are not covered by M3 semantic roles MUST be defined in the design system's `Colour.kt` file and mapped into `ColorScheme` or an `AppColours` extension.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates DS-THEME-02 — Brand-specific colors that are not covered by M3 semantic roles MUST be defined in the design system's `Colour.kt` file and mapped into `ColorScheme` or an `AppColours` extension.
```

Never define brand colors inline.

### Alpha constants

```kotlin
object Alpha {
    val disabled     = 0.38f   // disabled components
    val textDisabled = 0.60f   // disabled text (higher readability)
    val focused      = 0.12f   // focus indicators
    val pressed      = 0.12f   // press states
}
```

```rule
id: DS-THEME-08
statement: Use `Alpha` constants — never hardcode transparency values.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates DS-THEME-08 — Use `Alpha` constants — never hardcode transparency values.
```

---

## Typography

```rule
id: DS-THEME-03
statement: Use `MaterialTheme.typography` — never hardcode `fontSize`, `fontWeight`, or `lineHeight` in components.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates DS-THEME-03 — Use `MaterialTheme.typography` — never hardcode `fontSize`, `fontWeight`, or `lineHeight` in components.
```

| Need | Use |
|------|-----|
| Screen title | `MaterialTheme.typography.titleLarge` |
| Section header | `MaterialTheme.typography.titleMedium` |
| Body text (default) | `MaterialTheme.typography.bodyMedium` |
| Large body / reading | `MaterialTheme.typography.bodyLarge` |
| Small / caption | `MaterialTheme.typography.bodySmall` |
| Button label | `MaterialTheme.typography.labelLarge` |
| Chip / tag | `MaterialTheme.typography.labelMedium` |
| Hint / caption small | `MaterialTheme.typography.labelSmall` |

Customise if needed:
```kotlin
MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.Bold)
```

---

## Spacing

```rule
id: DS-THEME-04
statement: Use `Spacing` constants — never hardcode dp values in padding or spacer sizes.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates DS-THEME-04 — Use `Spacing` constants — never hardcode dp values in padding or spacer sizes.
```

```kotlin
object Spacing {
    val micro   = 2.dp    // minimal (rare)
    val mini    = 4.dp    // tight, between related items
    val small   = 8.dp    // default small
    val medium  = 16.dp   // default (most common)
    val large   = 24.dp   // between sections
    val xLarge  = 32.dp
    val xxLarge = 48.dp
}
```

```kotlin
// ✅ Correct
Column(modifier = Modifier.padding(Spacing.medium)) {
    Text("Item 1")
    Spacer(Modifier.height(Spacing.small))
    Text("Item 2")
}

// ❌ Wrong
Column(modifier = Modifier.padding(16.dp)) {
    Text("Item 1")
    Spacer(Modifier.height(8.dp))
    Text("Item 2")
}
```

---

## Dimension Constants

```rule
id: DS-THEME-05
statement: Use dimension constants for corners, elevations, and layout sizes.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates DS-THEME-05 — Use dimension constants for corners, elevations, and layout sizes.
```

```kotlin
object Corners {
    val checkbox = 4.dp
    val tab      = 8.dp
    val button   = 8.dp
    val chip     = 16.dp
    val card     = 16.dp
}

object Elevations {
    val tab      = 4.dp
    val card     = 4.dp
    val dialog   = 8.dp
    val dropdown = 16.dp
}

object Layout {
    val buttonHeight = 48.dp
    val toolbarHeight = 56.dp
    val textFieldHeight = 64.dp
}
```

---

## Light and Dark Theme Support

```rule
id: DS-THEME-06
statement: All components MUST support both light and dark themes without hardcoded theme-specific values.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates DS-THEME-06 — All components MUST support both light and dark themes without hardcoded theme-specific values.
```

```kotlin
// ✅ Correct — adapts automatically
Box(modifier = Modifier.background(MaterialTheme.colorScheme.surface)) {
    Text(text = "Content", color = MaterialTheme.colorScheme.onSurface)
}

// ❌ Wrong — hardcodes theme-specific color
val bg = if (isSystemInDarkTheme()) Color(0xFF1E1E1E) else Color(0xFFF5F5F5)
```

Always create a dark-mode preview alongside the default preview (see `PLAT-MOB-DS-COMPONENT`).

---

## Component Parameters Default to Theme Values

```rule
id: DS-THEME-07
statement: Customization parameters MUST default to theme values, not hardcoded colors.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates DS-THEME-07 — Customization parameters MUST default to theme values, not hardcoded colors.
```

```kotlin
@Composable
fun AppCard(
    modifier: Modifier = Modifier,
    containerColor: Color = MaterialTheme.colorScheme.surface,     // ✅ theme default
    contentColor: Color = MaterialTheme.colorScheme.onSurface,     // ✅ theme default
    elevation: Dp = Elevations.card
) { ... }
```

---

## Adding New Theme Constants

Add to theme files when a value is used in 3+ places or is part of a design spec.

| Type | File |
|------|------|
| Colors | `theme/Colour.kt` |
| Typography | `theme/Typography.kt` |
| Spacing, sizes, corners, elevations | `theme/Dimens.kt` |
| ColorScheme mapping | `theme/Theme.kt` |

```rule
id: DS-THEME-10
statement: New constants MUST go in theme files — never define them in component files.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates DS-THEME-10 — New constants MUST go in theme files — never define them in component files.
```

---

## Validation Checklist

### Colors
- [ ] Uses `MaterialTheme.colorScheme` — no hardcoded colors (DS-THEME-01)
- [ ] Custom brand colors in `Colour.kt` (DS-THEME-02)
- [ ] Semantic `on*` colors paired with their surface color
- [ ] Alpha values use `Alpha` constants (DS-THEME-08)
- [ ] Component supports light and dark themes (DS-THEME-06)

### Typography
- [ ] Uses `MaterialTheme.typography` — no hardcoded fontSize (DS-THEME-03)

### Spacing & Dimensions
- [ ] Uses `Spacing` constants — no hardcoded dp for padding/spacing (DS-THEME-04)
- [ ] Uses `Layout`/`Corners`/`Elevations` constants (DS-THEME-05)
- [ ] Uses `IconSizes` for icon dimensions (DS-ICON-04)

### Theme Integration
- [ ] Parameters default to theme values (DS-THEME-07)
- [ ] No `isSystemInDarkTheme()` for layout colors (DS-THEME-06)
- [ ] New constants in theme files, not component files (DS-THEME-10)
