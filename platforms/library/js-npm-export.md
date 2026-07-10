---
id: PLAT-LIB-JS-EXPORT
type: guide
layer: platform
platform: [library]
architecture: [all]
requires: [PLAT-LIB-KMP]
related: [PLAT-MOB-KMP-WEB]
tags: [kotlin-js, npm, typescript, jsexport, dts, esmodules, wasmjs]
status: active
---

# Kotlin/JS → npm/TypeScript Export

> **Provenance:** Written from `arrow-http`'s `workflows/active/patch-support-and-js-target.md`
> Phase 2 (in the `arrow-http` repo, not this one) — the first project using this framework to
> actually add a Kotlin/JS library-mode target and attempt `@JsExport`. Verified against Kotlin
> Gradle plugin **2.1.0** specifically; re-verify before assuming these mechanics are unchanged
> on a newer Kotlin version (the `webMain` situation below, in particular, is version-specific).

## Library-mode `js { }` target block (confirmed working, Kotlin 2.1.0)

```kotlin
js {
    browser()
    nodejs()
    binaries.library()
    useEsModules()
    generateTypeScriptDefinitions()
}
```

- `binaries.library()` — produces an npm-consumable library output instead of an app bundle.
  Confirmed via `./gradlew :module:jsBrowserProductionLibraryDistribution`, which writes ESM
  `.mjs` files plus a `.d.ts` to `build/dist/js/productionLibrary/`.
- `useEsModules()` — emits ES modules. Correct default for Vite/webpack-bundler consumers using
  `moduleResolution: "bundler"` (the motivating use case here — see below); a plain CommonJS
  Node consumer would omit this, but that wasn't this project's need.
- `generateTypeScriptDefinitions()` — emits the `.d.ts`. The compiler also runs a
  `jsProductionLibraryValidateGeneratedByCompilerTypeScript` task as part of the distribution
  task graph, which is a real, independent check (not just "the task didn't crash") worth
  treating as the actual verification signal.
- With **no** `@JsExport`-annotated declarations anywhere in the module, the generated `.d.ts`
  is not empty-file — it still contains a `Nullable<T>` type alias and (if the module uses
  `Map`/similar) a generic `KtMap<K, V>` wrapper interface, emitted unconditionally as part of
  the Kotlin/JS stdlib bridging, even with zero exported types.

## `@JsExport`: what actually exports, verified per-type

Spiked directly against `arrow-http`'s real public types (`HttpHeaders`, `ApiResponse`, the
`HttpException` sealed hierarchy, `HttpRequestExecutor`):

| Type shape | Result |
|---|---|
| Plain data class, simple properties | Exports cleanly as a TS class with a `copy`/`equals`/`hashCode`/`toString` surface. |
| Overloaded methods differing only by parameter type (e.g. two `plus(...)` operators) | **Compile error** (not a warning) — both generate the same JS-visible name and collide. Fix: `@JsName("distinctName")` on all but one overload. |
| `Map<K, V>` parameter/property | Exports as `KtMap<K, V>` (a generated wrapper interface), **not** a native TS `Map`/`Record`. Usable via `.asJsReadonlyMapView()`, but not a drop-in `Record<string,string>` for a TS consumer — worth a thin adapter if ergonomics matter. |
| `Pair<A, B>` parameter/property | **Does not export cleanly.** Compiles with a `NON_EXPORTABLE_TYPE` warning (not an error) and the generated `.d.ts` types the parameter as `any/* Pair<...> */` — real, unrecoverable type-safety loss for that member specifically. |
| `ByteArray` / `ByteArray?` | Exports as `Int8Array` / `Nullable<Int8Array>`. Clean, no warnings. |
| `sealed class` hierarchy | The base class and **each subclass individually** must carry `@JsExport` — it is **not inherited** by subtypes. When every subclass is annotated, the generated `.d.ts` correctly preserves the TS `extends` chain. |
| Interface or class with any `suspend fun` member | **Hard compile error**: `Declaration of such kind (suspend function) cannot be exported to JavaScript.` This is unconditional — there is no workaround via annotation or Gradle flag. Any type whose public surface includes suspend functions (e.g. the main request-executing interface of an HTTP library) **cannot be `@JsExport`-ed as-is**. |

**Practical takeaway:** plan for a JS/TS-facing library's exported surface to be a subset of
the full multiplatform public API — typically the *data* types (requests/responses/errors),
not the *suspend-based* entry points. A TypeScript-facing wrapper that exposes
`Promise`-returning methods over the suspend-based executor is the correct next step for full
coverage, but is a separate, unbuilt piece of work — don't assume it falls out for free once
the target compiles.

## Critical constraint: `@JsExport` cannot live in shared `commonMain` source

This is the most important, non-obvious finding, and the reason `arrow-http` shipped **no**
`@JsExport` annotations in 1.2.0 despite spiking them successfully in isolation:

`@JsExport`, `@JsName`, and `ExperimentalJsExport` are only resolvable while the compiler is
actually compiling for the `js` target. Adding these annotations to a class in `commonMain` —
even though `commonMain` compiles to every target — breaks compilation for **every other
target**, including JVM, Android, iOS, and (surprisingly) even `wasmJs`, with
`Unresolved reference: JsExport`-style errors. This is easy to miss if you only run
`compileKotlinJs` after adding the annotation, since that specific target succeeds.

**Implication:** you cannot simply annotate an existing shared multiplatform type to export
it to JS. Real support requires one of:
- A `jsMain`-only wrapper/wrapper-function layer that re-exposes the shared type's shape
  without annotating the shared declaration itself, or
- An `expect`/`actual` boundary where the JS `actual` is a distinct, `@JsExport`-annotated
  type, kept in sync with the common one.

Neither was built in `arrow-http` 1.2.0 — this document exists to save the next project from
rediscovering the "just add `@JsExport` to the commonMain class" dead end from scratch.

## `js` + `wasmJs` sharing a source set (`webMain`)

On Kotlin **2.1.0** (this project's pin), manually creating an intermediate `webMain` source
set — `val webMain by creating { dependsOn(commonMain.get()) }`, then `jsMain.dependsOn(webMain)`
/ `wasmJsMain.dependsOn(webMain)` — compiles the web targets correctly, **but** the Kotlin
Gradle plugin detects the explicit `dependsOn()` edges and disables its **default hierarchy
template for the entire module** as a safety measure. That default template is what
automatically wires `iosMain` to `iosX64Main`/`iosArm64Main`/`iosSimulatorArm64Main` — losing
it silently drops `iosMain` from every iOS compilation (`compileKotlinIosX64` etc. report no
warning, just quietly stop including `iosMain`'s sources). This is a real regression risk that
won't surface as a build failure — it surfaces as missing `actual` implementations at link time
or, on a Linux CI host that already can't run the iOS link step, not at all.

**Verified fallback:** duplicate the shared platform code (e.g. an identical `createHttpClient()`
`actual` in both `jsMain` and `wasmJsMain`) with a comment on each file pointing at its sibling.
Not elegant, but doesn't risk the rest of the target matrix.

**Kotlin 2.2.20+** adds an automatic `webMain`/`webTest` grouping for `js`+`wasmJs` under the
default hierarchy template (KT-75480) with no manual `dependsOn()` required — this removes the
whole problem. Re-evaluate collapsing the duplication once a project on this framework upgrades
past that version.

## Gradle infrastructure pitfalls when adding a `js` target alongside `wasmJs`

Two Kotlin Gradle plugin bugs surfaced specifically from having **both** `js` and `wasmJs`
targets declared, that don't show up with either target alone:

- **KT-69996** — if the root `build.gradle.kts` manually registers a `clean` task
  (`tasks.register("clean", Delete::class) { ... }`, a common Android Studio template default),
  adding a real `js` target causes Kotlin's Node.js root plugin to also try applying the Gradle
  `base` plugin, which fails with `Cannot add task 'clean' as a task with that name already
  exists`. Fix: apply `base` explicitly in the `plugins {}` block and configure `tasks.clean {}`
  instead of registering a new task.
- A related task-name collision can occur for any other manually-registered root-project task
  that the Node.js/Yarn root plugin also wants to own (e.g. a `rootPackageJson` stub task added
  to support composite-build consumers before this project had any real JS npm dependencies) —
  the fix pattern is the same: defer registration and check `tasks.findByName(...) == null`
  first, or don't register the stub if a real target now provides the task for real.

## npm publishing

Deliberately **not** covered by this document yet: `arrow-http` 1.2.0 only got the target
building and `.d.ts`-capable. `binaries.library()` + Maven Central publishing via the
`vanniktech` plugin does **not** also publish to npm — that's a fully separate pipeline
(different registry, different auth, an open question of whether the npm package version needs
to track the Maven artifact version 1:1). This needs a deliberate decision when a project
actually wires up an npm publish step, not an assumption carried over from this document.

## Motivating use case

The concrete driver for `arrow-http` doing this at all: `ampm-backend`'s OpenAPI-based
generated-API-client exploration wants both a Kotlin client (consumed by KMP apps) and a
TypeScript client (consumed by a Vite/React web dashboard) without maintaining two independent
OpenAPI→language codegen pipelines. Making `arrow-http`'s abstractions reachable from
TypeScript is what lets a single generated Kotlin client, built on this library, also serve the
TypeScript side — the codegen itself is unbuilt; this document only covers what makes the
*transport* capable of being reached from both language consumers.
