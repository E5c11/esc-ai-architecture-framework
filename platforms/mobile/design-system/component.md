---
id: PLAT-MOB-DS-COMPONENT
type: guide
layer: platform
platform: [mobile]
architecture: [all]
requires: [PLAT-MOB-COMPOSE, PLAT-MOB-DS-THEME, PLAT-MOB-DS-ICONS]
related: [ARCH-PC-VIEW, PLAT-MOB-DS-IMAGES]
tags: [design-system, compose, component, m3, material3, preview, accessibility, kmp]
---

# Design System — Adding a New Component

## Critical Rule: Design System is the Only M3 Import Location

```rule
id: PLAT-MOB-DS-M3-01
statement: The design system module is the ONLY place where Material 3 components are imported and used directly.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-DS-M3-01 — The design system module is the ONLY place where Material 3 components are imported and used directly.
```

Feature modules MUST NOT import from `androidx.compose.material3` (except for `MaterialTheme` token access). All Material 3 components are wrapped here with themed defaults.

This ensures:
- Consistent styling across the app
- Single point of change for theme updates
- Easy migration path between Material versions
- Features automatically follow design language without manual configuration

---

## Prerequisites

Before creating a new component:
- [ ] Component is needed by multiple features (not feature-specific)
- [ ] Component doesn't already exist in M3 or the base component library
- [ ] A wrapper does not already exist in the design system module

---

## Decision Tree

```
Need new component?

├─ Does a design system wrapper already exist?
│  └─ YES → Use existing wrapper
│
└─ NO → Does Material 3 have a base component?
        ├─ YES → Create wrapper (WRAPPER PATH)
        └─ NO → Create custom (CUSTOM PATH)

WRAPPER PATH: wrap M3 component with themed defaults
CUSTOM PATH: build from Compose primitives using theme tokens only
```

---

## Component Signature Template

```kotlin
@Composable
fun ComponentName(
    modifier: Modifier = Modifier,          // Rule DS-STRUCTURE-02: always first, always has default
    // State parameters (what the component displays)
    value: String,
    // Callback parameters
    onValueChange: (String) -> Unit,
    // Customization with theme defaults
    containerColor: Color = MaterialTheme.colorScheme.surface,
    enabled: Boolean = true,               // Rule DS-STRUCTURE-04: required for interactive components
) {
    // implementation
}
```

**Rules:**
- **DS-STRUCTURE-01:** `@Composable` annotation required
- **DS-STRUCTURE-02:** `modifier: Modifier = Modifier` MUST be first parameter
- **DS-STRUCTURE-03:** State hoisted via parameters, no internal mutable state for business data
- **DS-STRUCTURE-04:** Interactive components MUST have `enabled: Boolean = true`
- **DS-STRUCTURE-05:** `modifier` MUST be applied to the root element only
- **DS-STRUCTURE-08:** No business logic in component

---

## Wrapper Component Example

```kotlin
@Composable
fun AppButton(
    modifier: Modifier = Modifier,
    text: String,
    onClick: () -> Unit,
    enabled: Boolean = true,
    containerColor: Color = MaterialTheme.colorScheme.primary
) {
    Button(
        onClick = onClick,
        modifier = modifier,
        enabled = enabled,
        colors = ButtonDefaults.buttonColors(  // DS-M3-02: use *Defaults classes
            containerColor = containerColor
        )
    ) {
        Text(text)
    }
}
```

---

## Custom Component Example

```kotlin
@Composable
fun AppLabel(
    modifier: Modifier = Modifier,
    text: String,
    backgroundColor: Color = MaterialTheme.colorScheme.surface,   // DS-THEME-01
    textColor: Color = MaterialTheme.colorScheme.onSurface
) {
    Box(
        modifier = modifier
            .background(
                color = backgroundColor,
                shape = RoundedCornerShape(Corners.chip)           // DS-THEME-05
            )
            .padding(horizontal = Spacing.medium, vertical = Spacing.small)
    ) {
        Text(
            text = text,
            style = MaterialTheme.typography.labelMedium,          // DS-THEME-03
            color = textColor
        )
    }
}
```

---

## Accessibility

```kotlin
// Icons must have contentDescription (DS-A11Y-01)
Icon(imageVector = AppIcons.Info, contentDescription = "Information")

// Interactive elements need minimum 48dp touch target (DS-A11Y-02)
IconButton(modifier = Modifier.sizeIn(minWidth = 48.dp, minHeight = 48.dp)) { }

// Use semantic colors for contrast — DS-A11Y-03
Text(text = "Label", color = MaterialTheme.colorScheme.onSurface)

// Complex components: add semantic modifiers
Box(modifier = Modifier.semantics {
    stateDescription = if (checked) "Checked" else "Unchecked"
    role = Role.Checkbox
})
```

---

## State Variants

For components with multiple visual states (enabled/disabled, selected/unselected, loading/error):

```kotlin
@Composable
fun AppLoadingButton(
    modifier: Modifier = Modifier,
    text: String,
    onClick: () -> Unit,
    enabled: Boolean = true,
    isLoading: Boolean = false
) {
    Button(onClick = onClick, modifier = modifier, enabled = enabled && !isLoading) {
        if (isLoading) {
            CircularProgressIndicator(
                modifier = Modifier.size(IconSizes.medium),
                color = MaterialTheme.colorScheme.onPrimary
            )
        } else {
            Text(text)
        }
    }
}
```

State feedback patterns:
- **Disabled:** Apply `Alpha.disabled` (0.38f) or `Alpha.textDisabled` (0.6f)
- **Selected:** Change background to `primaryContainer`
- **Loading:** Show `CircularProgressIndicator`, disable interaction
- **Error:** Use `colorScheme.error` and `colorScheme.onError`

---

## Preview Functions

```kotlin
@Preview
@Composable
fun ComponentNamePreview() {         // DS-NAMING-03
    AppTheme {                        // DS-STRUCTURE-07: wrap in app theme
        Box(
            modifier = Modifier
                .background(MaterialTheme.colorScheme.background)
                .padding(Spacing.medium)
        ) {
            ComponentName(value = "Example", onValueChange = {})
        }
    }
}

@Preview
@Composable
fun ComponentNameDisabledPreview() {
    AppTheme {
        Box(modifier = Modifier.background(MaterialTheme.colorScheme.background).padding(Spacing.medium)) {
            ComponentName(value = "Disabled", onValueChange = {}, enabled = false)
        }
    }
}

@Preview
@Composable
fun ComponentNameDarkPreview() {
    AppTheme(isDarkTheme = true) {
        Box(modifier = Modifier.background(MaterialTheme.colorScheme.background).padding(Spacing.medium)) {
            ComponentName(value = "Dark mode", onValueChange = {})
        }
    }
}
```

**Rules:**
- **DS-STRUCTURE-06:** At least one preview per component; additional previews for significant states
- **DS-STRUCTURE-07:** All previews wrapped in the app theme
- **DS-NAMING-03:** Preview named `{Component}Preview`, state previews `{Component}{State}Preview`

---

## Validation Checklist

### Structure & Naming
- [ ] File in `components/base/` for base components
- [ ] `@Composable` annotation (DS-STRUCTURE-01)
- [ ] `modifier: Modifier = Modifier` as first parameter (DS-STRUCTURE-02)
- [ ] State hoisted via parameters (DS-STRUCTURE-03)
- [ ] `enabled` parameter for interactive components (DS-STRUCTURE-04)
- [ ] `modifier` applied to root element only (DS-STRUCTURE-05)
- [ ] No business logic in component (DS-STRUCTURE-08)

### Theme Integration
- [ ] Uses `MaterialTheme.colorScheme` for colors (DS-THEME-01)
- [ ] Uses `MaterialTheme.typography` for text (DS-THEME-03)
- [ ] Uses `Spacing`/`Layout`/`Corners` from dimension constants (DS-THEME-04, DS-THEME-05)
- [ ] Parameters default to theme values (DS-THEME-07)
- [ ] Uses `Alpha` constants for transparency (DS-THEME-08)
- [ ] Supports light and dark themes (DS-THEME-06)

### Material 3
- [ ] Uses M3 component if available (DS-M3-01)
- [ ] Uses `*Defaults` classes for styling (DS-M3-02)

### Accessibility
- [ ] Icons have `contentDescription` (DS-A11Y-01)
- [ ] Touch targets minimum 48dp (DS-A11Y-02)
- [ ] Color contrast meets WCAG AA (DS-A11Y-03)

### Multiplatform
- [ ] Component in `commonMain` (DS-KMP-01)
- [ ] No platform-specific APIs used

### Previews
- [ ] At least one preview function (DS-STRUCTURE-06)
- [ ] Previews wrapped in app theme (DS-STRUCTURE-07)
- [ ] Previews show different states if applicable
