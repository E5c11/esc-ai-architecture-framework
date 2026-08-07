---
id: PLAT-MOB-DS-IMAGES
type: guide
layer: platform
platform: [mobile]
architecture: [all]
requires: [PLAT-MOB-COMPOSE, PLAT-MOB-DS-THEME, PLAT-MOB-KMP-WEB]
related: [PLAT-MOB-DS-COMPONENT]
tags: [design-system, images, coil, async-image, placeholder, kmp, accessibility]
status: active
---

# Design System — Image Components

## Overview

The design system provides abstracted image components that wrap the underlying image
loading library (Coil 3). Feature modules use these abstractions — they never import
Coil directly.

This allows:
- Consistent image loading behaviour across the app
- Easy replacement of the image library
- Centralized caching and error handling configuration

---

## Rules

- **DS-IMAGE-01 (hard):** All image loading MUST use design system image components
- **DS-IMAGE-02 (hard):** Feature modules MUST NOT import Coil directly
- **DS-IMAGE-03 (hard):** Always provide `contentDescription` for accessibility
- **DS-IMAGE-04 (hard):** Always define placeholder and error states
- **DS-IMAGE-05 (hard):** Use `ImageSizes` constants from dimension tokens — never hardcode dp

---

## Component Types

| Component | Purpose |
|-----------|---------|
| `AppAsyncImage` | Primary component for loading remote images (URLs) |
| `AppLocalImage` | Local drawable resources |
| `AppCircularImage` | Circular crop — avatars, profiles |

Create additional specialized variants (e.g. `AppPropertyImage`, `AppHeroImage`) as
needed for fixed aspect-ratio or domain-specific shapes.

---

## Usage

```kotlin
// Basic URL image
AppAsyncImage(
    imageUrl = item.imageUrl,
    contentDescription = "Item image",
    modifier = Modifier.size(ImageSizes.preview)
)

// With placeholder and error
AppAsyncImage(
    imageUrl = imageUrl,
    contentDescription = "User profile",
    placeholder = AppImagePlaceholder.Icon(AppIcons.Person),
    error = AppImagePlaceholder.Icon(AppIcons.BrokenImage),
    modifier = Modifier.size(IconSizes.xLarge)
)

// Circular avatar
AppCircularImage(
    imageUrl = user.avatarUrl,
    contentDescription = "Profile picture",
    size = IconSizes.xLarge,
    placeholder = AppImagePlaceholder.Icon(AppIcons.Person)
)
```

---

## Placeholder Types

`AppImagePlaceholder` is a sealed class with three variants:

```kotlin
sealed class AppImagePlaceholder {
    data class Icon(
        val icon: ImageVector,
        val tint: Color? = null   // null = use MaterialTheme default
    ) : AppImagePlaceholder()

    data class Color(val color: androidx.compose.ui.graphics.Color) : AppImagePlaceholder()

    object Shimmer : AppImagePlaceholder()  // animated shimmer/sweep effect
}
```

---

## Size Constants

Always use size constants — never hardcode:

```kotlin
object ImageSizes {
    val thumbnail = 80.dp
    val preview   = 128.dp
    val small     = 64.dp
    val medium    = 120.dp
    val large     = 200.dp
    val avatar    = 48.dp
    val avatarLarge = 72.dp
}
```

---

## KMP / Web Considerations

Coil requires a different network engine per platform:

```kotlin
// build.gradle.kts
androidMain {
    dependencies { implementation(libs.coil.network.okhttp) }
}
wasmJsMain {
    dependencies { implementation(libs.coil.network.ktor) }
}
iosMain {
    dependencies {
        implementation(libs.coil.network.ktor)
        implementation(libs.ktor.client.darwin)
    }
}
```

No code changes needed in components — Coil 3 detects the engine automatically.
See `PLAT-MOB-KMP-WEB` for source set placement rules.

**Rule DS-IMAGE-IOS-01 (hard):** iOS remote-image loading MUST include a compatible
Ktor/Coil engine and be proven by a simulator image-load smoke test. Common compilation
alone does not prove engine availability.

---

## Image Transformations

For images that need visual effects, wrap with a transform component:

```kotlin
AppTransformedImage(
    imageUrl = url,
    contentDescription = "Blurred background",
    transformation = ImageTransformation.Blur(radius = 16.dp)
)

AppTransformedImage(
    imageUrl = url,
    contentDescription = "Dimmed image",
    transformation = ImageTransformation.Darken(alpha = 0.4f)
)
```

---

## Validation Checklist

- [ ] Image component imported from design system module — not Coil (DS-IMAGE-01, DS-IMAGE-02)
- [ ] `contentDescription` provided for all images (DS-IMAGE-03)
- [ ] `placeholder` defined for loading state (DS-IMAGE-04)
- [ ] Error state handled (DS-IMAGE-04)
- [ ] Size uses `ImageSizes` or `IconSizes` constants (DS-IMAGE-05)
- [ ] `modifier` applied for layout control

---

## Common Mistakes

```kotlin
// WRONG — direct Coil import in feature module
import coil3.compose.AsyncImage

// WRONG — hardcoded size
Modifier.size(100.dp)

// WRONG — missing placeholder
AppAsyncImage(imageUrl = url, contentDescription = "Image")

// WRONG — missing contentDescription
AppAsyncImage(imageUrl = url, contentDescription = null)
```
