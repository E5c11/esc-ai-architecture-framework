# AI Engineering Framework v2 Vision

## Purpose

Transform the AI Engineering Framework (previously the "prompt library")
into a provider-agnostic, reusable engineering framework that can
support multiple projects, architectures and AI providers while
remaining deterministic and maintainable.

------------------------------------------------------------------------

# Core Principles

## Provider Agnostic

The framework must not depend on Claude Code, Codex, Gemini or any other
specific AI provider.

The framework should instead define:

-   Engineering knowledge
-   Engineering standards
-   Architecture rules
-   Feature Orchestrators
-   Quality Gates
-   Retrieval metadata

The AI model becomes an interchangeable execution engine.

------------------------------------------------------------------------

## Architecture First

The framework should encode engineering principles rather than
technologies.

Examples:

-   Dependency Inversion
-   Low Coupling
-   High Cohesion
-   Clean Architecture
-   Testing philosophy
-   Documentation standards
-   Error handling

Technology-specific guidance should extend these principles instead of
replacing them.

------------------------------------------------------------------------

## Layered Framework

    Framework
    │
    ├── Core
    ├── Platforms
    ├── Architectures
    ├── Patterns
    ├── Quality Gates
    ├── Feature Orchestrators
    ├── Retrieval Metadata
    └── Schemas

------------------------------------------------------------------------

# Repository Structure

``` text
ai-engineering-framework/
│
├── core/
├── platforms/
│   ├── mobile/
│   ├── backend/
│   ├── web/
│   └── cloud/
│
├── architectures/
│
├── patterns/
│
├── quality-gates/
│
├── feature-orchestrators/
│
├── schemas/
│
├── tools/
│
└── .github/workflows/
```

------------------------------------------------------------------------

# Project Knowledge

The framework only contains reusable knowledge.

Every project owns its own project-specific knowledge.

Example:

``` text
YouTube Clone
    .ai/
        project-profile.yaml
        project-rules/
        module-docs/
        ADRs/

AMPM
    .ai/
        project-profile.yaml
        project-rules/
        firestore/
        module-docs/
```

Project knowledge should never migrate into the central framework.

------------------------------------------------------------------------

# Project Profiles

Every project exposes a Project Profile.

Example

``` yaml
project: youtube

platform:
  mobile

language:
  kotlin

architecture:
  pragmatic-clean

state-management:
  mvvm

network:
  escape-network

database:
  room

cloud:
  none

backend:
  youtube-api
```

The profile determines which framework knowledge is retrieved.

------------------------------------------------------------------------

# Architecture Profiles

Projects may use different architectural styles.

Examples

-   Full Clean Architecture
-   Pragmatic Clean
-   Vertical Slice
-   Hexagonal
-   Backend Service
-   Serverless

The retrieval engine must select only the relevant architectural
guidance.

------------------------------------------------------------------------

# Retrieval (RAG)

The framework should move toward metadata-driven retrieval.

Instead of supplying the entire Knowledge Base, retrieve only
documentation relevant to:

-   Project Profile
-   Architecture
-   Platform
-   Phase
-   Pattern
-   Feature

Goal:

Small context.

High relevance.

Low token usage.

------------------------------------------------------------------------

# Feature Orchestrators

Rename TODOs to **Feature Orchestrators**.

A Feature Orchestrator should:

-   describe the implementation goal
-   define phases
-   define validation gates
-   reference required framework knowledge
-   reference project documentation

The Feature Orchestrator acts as the implementation orchestrator.

------------------------------------------------------------------------

# Rule Referencing

Documentation should explicitly reference implementation rules.

Example

-   Repository Pattern
-   Dependency Injection Rules
-   Testing Rules
-   Naming Rules

Rules should be structured and machine-readable where appropriate.

------------------------------------------------------------------------

# Metadata

Each document should include metadata.

Example

``` yaml
id:
type:
platform:
architecture:
requires:
related:
applies_to:
```

Metadata powers retrieval and validation.

------------------------------------------------------------------------

# CI/CD

Every commit should validate the framework.

Checks include:

-   Broken references
-   Missing documents
-   Invalid metadata
-   Duplicate IDs
-   Circular references
-   Schema validation
-   Retrieval index generation

The framework should behave like compilable documentation.

------------------------------------------------------------------------

# Long-Term Roadmap

## Phase 1

-   Restructure repository
-   Add metadata
-   Rename TODOs -\> Feature Orchestrators
-   Separate project knowledge

## Phase 2

-   Reference validation
-   Metadata validation
-   GitHub Actions

## Phase 3

-   Retrieval index generation
-   Local RAG experiments

## Phase 4

-   Framework API
-   AI provider integrations
-   Context service

------------------------------------------------------------------------

# Initial Validation Project

Use the YouTube Clone as the first consumer of the framework.

Goals

-   Validate project profiles.
-   Validate Feature Orchestrators.
-   Validate retrieval.
-   Compare Claude Code, Codex and Gemini.
-   Refine the framework from real usage rather than theory.
