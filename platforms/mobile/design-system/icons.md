---
id: PLAT-MOB-DS-ICONS
type: guide
layer: platform
platform: [mobile]
architecture: [all]
requires: [PLAT-MOB-COMPOSE, PLAT-MOB-DS-THEME]
related: [PLAT-MOB-DS-COMPONENT]
tags: [design-system, icons, imagevector, svg, compose, accessibility, kmp]
---

# Design System — Icons

## Overview

All icons are centralized in a singleton object (e.g. `AppIcons`). This provides:
- Single source of truth for all app icons
- Type safety with `ImageVector`
- Easy replacement of icons across the app
- Consistent naming

**Rule DS-ICON-01 (hard):** NEVER use Material Icons directly in components.
Always access icons through the centralized `AppIcons` object.

---

## Adding a Material Icon

```kotlin
object AppIcons {
    // Navigation
    val Dashboard: ImageVector = Icons.Filled.Dashboard
    val Settings: ImageVector = Icons.Filled.Settings

    // Directional (RTL-aware)
    val Back: ImageVector = Icons.AutoMirrored.Filled.ArrowBack
    val Forward: ImageVector = Icons.AutoMirrored.Filled.ArrowForward

    // Outlined variants
    val InfoOutlined: ImageVector = Icons.Outlined.Info
}
```

**Rule DS-ICON-02 (hard):** New icons MUST be added to the `AppIcons` object, not
used inline as `Icons.Filled.X` at the call site.

**Rule DS-ICON-03 (soft):** Choose the appropriate icon variant:
- **Filled:** Primary actions, selected states
- **Outlined:** Secondary actions, unselected states
- **AutoMirrored:** Directional icons (arrows) that must flip in RTL layouts

**Import rule:** Import only the specific icon symbols used — no wildcard imports.

---

## Creating Custom Icons

### Option 1: SVG → ImageVector (multiplatform)

Convert with a tool (e.g. `svg2compose`), then add to `AppIcons`:

```kotlin
object AppIcons {
    val CustomIcon: ImageVector = ImageVector.Builder(
        name = "CustomIcon",
        defaultWidth = 24.dp,
        defaultHeight = 24.dp,
        viewportWidth = 24f,
        viewportHeight = 24f
    ).apply {
        path(fill = SolidColor(Color.Black)) {
            // path data from SVG conversion
        }
    }.build()
}
```

### Option 2: Android XML drawable (platform-specific only)

Place in `androidMain/res/drawable/` and access via `painterResource`. Use only when
multiplatform support is not required.

---

## Using Icons in Components

```kotlin
// ✅ Correct
Icon(
    imageVector = AppIcons.Settings,
    contentDescription = "Settings",          // DS-A11Y-01
    modifier = Modifier.size(IconSizes.medium), // DS-ICON-04
    tint = MaterialTheme.colorScheme.primary  // DS-THEME-01
)

// ❌ Wrong
Icon(
    imageVector = Icons.Filled.Settings,  // violates DS-ICON-01
    contentDescription = "Settings",
    modifier = Modifier.size(24.dp),      // violates DS-ICON-04
    tint = Color.Blue                     // violates DS-THEME-01
)
```

---

## Icon Sizes

**Rule DS-ICON-04 (hard):** Always use `IconSizes` constants — never hardcode dp values.

| Constant | Value | Usage |
|----------|-------|-------|
| `IconSizes.small` | 16.dp | Small inline, decorative |
| `IconSizes.medium` | 24.dp | Standard (default) |
| `IconSizes.large` | 32.dp | Prominent icons |
| `IconSizes.xLarge` | 48.dp | Large touch targets |
| `IconSizes.xxLarge` | 64.dp | Avatar-sized |

---

## Accessibility

```kotlin
// Informative icon — always provide description
Icon(imageVector = AppIcons.Info, contentDescription = "Information")

// Decorative icon — explicitly null
Icon(imageVector = AppIcons.Divider, contentDescription = null)

// Icon-only interactive element — minimum 48dp touch target
IconButton(onClick = {}) {
    Icon(
        imageVector = AppIcons.Delete,
        contentDescription = "Delete item",    // required — button has no other label
        modifier = Modifier.size(IconSizes.medium)
    )
    // IconButton automatically provides the 48dp touch target
}
```

Use `null` contentDescription only when:
- Icon is purely decorative
- A nearby text label provides the context
- Icon is inside a button that already has a text label

---

## Disabled State

```kotlin
Icon(
    imageVector = AppIcons.Lock,
    contentDescription = "Locked",
    tint = MaterialTheme.colorScheme.onSurface.copy(alpha = Alpha.disabled) // DS-THEME-08
)
```

---

## Validation Checklist

- [ ] Icon added to `AppIcons` object (DS-ICON-02)
- [ ] Icon accessed via `AppIcons.{Name}`, not `Icons.Filled.{Name}` (DS-ICON-01)
- [ ] Appropriate variant chosen — `AutoMirrored` for directional icons (DS-ICON-03)
- [ ] Size uses `IconSizes` constants (DS-ICON-04)
- [ ] `contentDescription` provided or explicitly `null` with justification (DS-A11Y-01)
- [ ] Tint uses `MaterialTheme.colorScheme` (DS-THEME-01)
- [ ] Interactive icons have 48dp minimum touch target (DS-A11Y-02)
- [ ] No wildcard imports in `AppIcons.kt`
