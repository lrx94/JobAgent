# JobAgent - Instructions for AI Development Agents

## Mission

JobAgent is an AI-assisted job-search platform.

Its main responsibilities are:

- CV analysis;
- candidate profile generation;
- job collection from external providers;
- profile/job matching;
- market analysis;
- assisted learning;
- multi-user workspace management.

The project must remain deterministic, testable and explainable.

AI agents must improve the existing architecture rather than bypass it.

---

## Read before modifying code

Before any development task:

1. Read this `AGENTS.md`.
2. Read `ARCHITECTURE.md`.
3. Read `DEVELOPMENT_RULES.md`.
4. Read the current sprint specification in `SPRINTS/`.
5. Inspect the existing implementation.
6. Inspect existing tests covering the affected modules.
7. Produce a short implementation plan before modifying files.

Do not assume architecture from file names alone.

---

## Architectural direction

The preferred application architecture is:

Streamlit UI
    ↓
Workspace / application services
    ↓
Career / Learning / Market / CV
    ↓
Matching / Analysis
    ↓
Providers / repositories
    ↓
Persistent storage

The Workspace architecture is the preferred direction.

Legacy `app.py` behavior must remain functional unless a sprint explicitly removes or migrates it.

---

## Core modules

### `src/workspace`

Application-level orchestration and user isolation.

Do not duplicate business logic here.

### `src/career`

Career analysis, role detection, profile generation and career search workflow.

### `src/learning`

Assisted learning and human-reviewed suggestions.

Learning must never silently modify reference catalogs.

### `src/market`

Market statistics and skill-demand analysis.

### `src/matching`

Candidate/job matching and scoring.

### `src/analysis`

Structured candidate/job analysis and multidimensional scoring.

### `src/ai`

Shared extraction, normalization, synonym dictionaries and semantic helpers.

Prefer shared skill knowledge over duplicated dictionaries.

### `src/providers`

External job providers.

Provider failures must not crash the complete search workflow.

### `src/cvs` / `src/cv`

CV library, parsing and analysis.

### `src/storage`

Persistence and user paths.

### `src/auth`

Authentication, authorization and user context.

---

## Critical architectural rules

### No duplicated knowledge

Do not introduce another skill synonym dictionary if a shared one already exists.

When several catalogs overlap, prefer consolidation or an adapter.

### Preserve user isolation

New Workspace features must respect `UserContext` and user-specific storage.

### Preserve explainability

Matching, filtering and learning decisions must remain inspectable.

Do not hide important business decisions inside opaque helpers.

### Provider resilience

One failing provider must not destroy valid results from other providers.

The UI and result models should expose partial-search information when appropriate.

### Learning safety

Accepted Learning suggestions are human-approved observations.

Do not automatically publish them into reference catalogs unless a dedicated controlled workflow explicitly implements that behavior.

---

## Git workflow

One branch per sprint.

Branch convention:

`feature/vX.Y.Z-short-description`

Never develop directly on `develop`.

During a sprint:

- multiple commits are allowed;
- commits must remain understandable;
- do not mix unrelated refactors with the sprint.

Do not merge into `develop` automatically unless explicitly requested.

---

## Testing policy

Every behavior change requires tests.

Before delivery:

1. run targeted tests;
2. run tests for directly dependent modules;
3. run the complete unit-test suite when reasonably possible.

Never claim tests passed unless they were actually executed.

If a test cannot run because of an external dependency, explain why.

Functional Streamlit and real-provider validation are performed separately.

---

## Change policy

Prefer:

- small changes;
- explicit models;
- dependency injection;
- shared services;
- deterministic logic;
- backwards-compatible migrations.

Avoid:

- large unrelated refactors;
- hidden global state;
- duplicated business logic;
- direct UI access to persistence;
- catching `Exception` without translating or preserving useful diagnostic information.

---

## Completion report

At the end of every sprint, provide:

### Summary
What changed and why.

### Files changed
List each modified or created file.

### Tests
Commands executed and results.

### Risks
Known limitations or follow-up work.

### Functional validation
Exact steps the Product Owner should run locally.

### Git
Current branch and commit summary.

Do not commit automatically unless the sprint specification explicitly authorizes it.