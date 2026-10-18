---
id: ARCH-WEB-APP-LAYERS
type: overview
layer: architectures
platform: [web]
architecture: [web-app]
requires: [ARCH-WEB-APP, ARCH-WEB-APP-DOMAIN, ARCH-WEB-APP-DATASOURCE, ARCH-WEB-APP-REPOSITORY, ARCH-WEB-APP-USECASE, ARCH-WEB-APP-HOOK, ARCH-WEB-APP-COMPONENT, ARCH-WEB-APP-COMPOSITION, ARCH-WEB-APP-FEATURE-STRUCTURE, ARCH-WEB-APP-MODULES, ARCH-WEB-APP-ERR-CLASSES, ARCH-WEB-APP-ERR-FLOW, PLAT-WEB-REACT-PATTERNS, PLAT-WEB-STATE, PLAT-WEB-DS-THEME, QG-WEB-TESTING]
related: [ORCH-WEB-APP, PLAT-WEB-NEXT, PLAT-WEB-NEXT-STATIC, PLAT-WEB-NEXT-DATA]
tags: [web-app, layers, index, entry-point, reading-guide]
status: active
---

# Web App: The Layer Documents

The one entry point for the `web-app` architecture. It owns no rules. It exists so a project
or an agent can name a single document ("this repository follows `ARCH-WEB-APP-LAYERS`") and
receive the overview and every layer document through the `requires` chain, in layer order,
rather than listing thirteen IDs and missing one.

Read `ARCH-WEB-APP` first: it owns the layer stack, the dependency rules
(`ARCH-WEB-APP-DEP-01` to `-08`) and the layer-inclusion decisions. Each layer document then
owns everything else about its layer.

## Which document, for which task

| You are about to… | Read |
|---|---|
| Decide where a new file goes, or add a feature | `ARCH-WEB-APP-FEATURE-STRUCTURE` |
| Add a rule, a transform or a calculation | `ARCH-WEB-APP-DOMAIN` |
| Read from or write to a provider (Firestore, REST, a callable, Postgres) | `ARCH-WEB-APP-DATASOURCE` |
| Combine two sources of one entity | `ARCH-WEB-APP-REPOSITORY` (check the threshold first) |
| Add a business operation that does more than forward a call | `ARCH-WEB-APP-USECASE` |
| Expose data to a screen | `ARCH-WEB-APP-HOOK` |
| Render it | `ARCH-WEB-APP-COMPONENT` |
| Build or change how things are wired, or touch configuration or SDK initialisation | `ARCH-WEB-APP-COMPOSITION` |
| Handle a failure, or decide what the user sees | `ARCH-WEB-APP-ERR-CLASSES`, `ARCH-WEB-APP-ERR-FLOW` |
| Log, report an error, record an operation, or send analytics | `ARCH-WEB-APP-OBS` |
| Split a large module, or share code with a function or script | `ARCH-WEB-APP-MODULES` |

## The runtime

A project declares `frameworks.runtime` in its profile (`ARCH-WEB-APP-RUNTIME-01`). The layer
documents hold for both runtimes and say where they differ. The platform guides that
differ by runtime are selected by that field:

| Runtime | Platform guides |
|---|---|
| `server` | `PLAT-WEB-NEXT-APP`, `PLAT-WEB-NEXT-APP-DEPLOY`, `PLAT-WEB-NEXT-DATA`, `PLAT-WEB-HTTP` |
| `static-export` | `PLAT-WEB-NEXT-STATIC`, `PLAT-WEB-NEXT-FIREBASE` |

Shared by both, and required by this document so an onboarded project receives them with the
architecture: `PLAT-WEB-REACT-PATTERNS`, `PLAT-WEB-STATE`, `PLAT-WEB-DS-THEME`, `QG-WEB-TESTING`
(and `PLAT-WEB-REACT`, through the Hook and Component documents). `PLAT-WEB-NEXT` comes from the
project's detected `ui: next`. The step-by-step recipe for a feature is `ORCH-WEB-APP`.

## Checking the architecture

The dependency rules are checkable. Generate a contract with
`esc-exec architecture profile generate <repository> <component> --template web-app` and run it
with `esc-exec architecture check` (see "Declaring the contract" in `ARCH-WEB-APP`).
