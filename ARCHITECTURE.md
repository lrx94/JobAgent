# JobAgent Architecture

## 1. Overview

JobAgent is a Python / Streamlit application for AI-assisted job search.

The project currently contains two application paths:

1. the historical Streamlit flow in `app.py`;
2. the newer multi-user Career Workspace in `pages/01_Career_Workspace.py`.

The architectural direction is to progressively converge on the Workspace model without breaking existing behavior.

---

## 2. Target layering

```text
Streamlit UI
    ↓
Workspace / Application Services
    ↓
Career / CV / Learning / Market
    ↓
Matching / Analysis
    ↓
Providers / Repositories
    ↓
JSON / PDF / SQLite


Dependencies should primarily move downward.

Business-domain modules must not depend on Streamlit.

3. Workspace

src/workspace

The Workspace is the preferred application façade.

Responsibilities:

bind services to one authenticated user;
orchestrate profile and CV workflows;
expose application use cases;
translate lower-level failures into Workspace errors.

The Workspace must not duplicate domain logic.

Long-term goal:

all Career Workspace use cases should be composed from one coherent Workspace object.

4. Career

src/career

Responsibilities:

detect candidate role families;
build search profiles;
select or recommend providers;
execute Career search workflows;
filter collected jobs for career relevance.

Important components:

JOB_ROLE_CATALOG
RoleDetector
CareerProfileBuilder
CVProfileService
UserCVProfileService
ProviderAdvisor
ProviderSelector
CareerSearchWorkflow
CareerSearchResult

The selected career role is important context and should not be lost between profile generation and job filtering.

5. CV

src/cv
src/cvs

Responsibilities:

PDF text extraction;
skill extraction;
CV storage;
CV analysis;
CV/profile associations;
deduplication.

The CV pipeline must tolerate PDF formatting such as line breaks inside multi-word skills.

6. Skills and AI knowledge

src/ai
src/skills
src/matching

JobAgent currently has multiple skill-related components.

The architectural direction is:

Shared canonical skill knowledge
        ↓
CV extraction
        ↓
Profile construction
        ↓
Job matching
        ↓
Market analysis
        ↓
Learning comparison

Canonical names, synonyms and aliases should not diverge between these stages.

A technical normalized identifier and a user-facing display label may eventually be separated.

7. Matching

src/matching

Responsibilities:

exact skill matching;
alias matching;
semantic/category matching;
skill-graph matching;
scoring.

MatchingEngine enriches each Job with:

score;
matched skills;
missing skills;
match details.

Matching must remain explainable.

8. Job services

src/services

JobService orchestrates:

SearchRequest construction;
provider collection;
aggregation;
deduplication;
matching;
persistence;
sorting.

A provider failure must not cancel valid results from other providers.

9. Providers

src/providers

Currently important providers include:

France Travail;
RemoteOK.

LinkedIn and Welcome to the Jungle may exist as code or future connectors but should not be considered operational unless actually wired into the default provider factory.

Provider selection and provider execution should progressively converge.

10. Market

src/market

Responsibilities:

skill-demand statistics;
source distribution;
skill gaps;
co-occurrences;
market portrait.

A market portrait must clearly distinguish:

all collected offers;
career-relevant offers;
partial provider results.
11. Learning

src/learning

Pipeline:

Jobs
 ↓
Learning observations
 ↓
Suggestion detection
 ↓
AssistedLearningService
 ↓
Suggestion repository
 ↓
Human decision

Statuses:

candidate;
accepted;
rejected;
ignored.

Learning is currently assisted, not autonomous.

Human feedback may later improve the Quality Gate, but accepted terms must not automatically mutate production catalogs without a controlled publication mechanism.

12. Authentication and storage

src/auth
src/storage

Workspace data is isolated by user.

Typical path:

data/users/<user_id>/

Any new Workspace persistence must preserve this isolation.

13. UI

app.py
pages/01_Career_Workspace.py
src/ui
src/workspace/ui

Streamlit pages should primarily:

gather input;
call application services;
render results.

Business rules should progressively move out of the large Career Workspace page.

14. Known architecture risks

Current known risks include:

historical and Workspace application paths coexist;
duplicated skill dictionaries / normalizers;
multiple equivalent models exist;
Career Workspace is large and orchestration-heavy;
provider selection does not always control actual provider execution;
selected Career role can be lost during Workspace search;
JSON, PDF and SQLite persistence are not transactionally unified;
unit coverage is stronger than true end-to-end coverage.

These risks should be improved incrementally, not through a single massive refactor.


---

# `DEVELOPMENT_RULES.md`

```markdown
# JobAgent Development Rules

## 1. General principles

Code must be:

- readable;
- typed;
- testable;
- deterministic where possible;
- explicit about errors;
- compatible with existing persisted data.

Prefer simple code over clever code.

---

## 2. Python

Use:

- Python 3.13 compatible syntax;
- type hints;
- `from __future__ import annotations` when consistent with the module;
- dataclasses for explicit value models where appropriate.

Avoid unnecessary dependencies.

---

## 3. Functions and classes

A function should have one primary responsibility.

Prefer dependency injection over construction of hidden dependencies.

Do not create a new abstraction unless it removes real duplication or establishes a useful contract.

---

## 4. Errors

Do not silently swallow important errors.

Provider-level failures should be isolated.

Application-level services should translate lower-level errors when useful while preserving diagnostic context using exception chaining.

Example:

```python
raise WorkspaceError(
    "Message utilisateur."
) from error
5. Skills and normalization

Skill comparisons must be case-insensitive.

Accent-insensitive matching is allowed when relevant.

Multi-word skills must tolerate whitespace and PDF line breaks.

Canonical values should remain stable.

Do not add another independent alias catalog without justification.

6. Matching

Matching changes must preserve:

exact-match priority;
protection against substring false positives;
explainability;
score compatibility where possible.

Semantic matches must not be silently treated as exact matches.

If semantic evidence is used by relevance filtering, that decision must be explicit and tested.

7. Providers

Always validate:

HTTP status;
content type when appropriate;
malformed response handling;
empty payloads.

External APIs must never be trusted to always return the expected JSON.

8. Persistence

Do not write outside the intended user or application storage root.

Do not change persisted JSON schemas without a compatibility strategy.

Atomic writes are preferred for JSON state.

9. Streamlit

Avoid business logic directly inside Streamlit rendering functions.

Be careful with reruns and st.session_state.

Actions changing persistent state must refresh displayed state consistently.

10. Tests

New behavior requires tests.

Prefer:

deterministic unit tests;
fake providers;
temporary directories;
explicit integration tests between internal components.

Do not require live external APIs for the normal unit-test suite.

11. Backwards compatibility

Before removing a field, model or service:

search all usages;
inspect persistence compatibility;
inspect tests;
provide migration or compatibility behavior when necessary.
12. Refactoring rule

A sprint should solve its stated problem.

Do not combine:

major architectural migration;
UI redesign;
unrelated cleanup;
feature implementation

unless the sprint explicitly calls for them.

13. Definition of Done

A change is done when:

code is implemented;
targeted tests pass;
dependent tests pass;
full tests have been run when practical;
no known regression is hidden;
functional validation steps are documented.

---

# `ROADMAP_AI.md`

Je garderais la roadmap volontairement courte pour éviter qu’elle devienne immédiatement obsolète :

```markdown
# JobAgent AI Roadmap

This document tracks technical/product directions involving AI-assisted development and intelligent JobAgent capabilities.

It is intentionally high level.

---

## v3.18 - Search and Career Quality

### v3.18.1 Finance CV Coverage

Status: completed

Goals:

- Finance skill extraction;
- CFO / financial-direction role detection;
- real Finance CV validation.

### v3.18.2 Search Quality

Status: active

Goals:

- align skill knowledge between CV and matching pipelines;
- improve job relevance filtering;
- explain rejected jobs;
- preserve IT matching behavior.

### v3.18.3 Provider Reliability

Candidate scope:

- France Travail malformed/non-JSON responses;
- richer provider diagnostics;
- partial-search quality indication.

---

## v3.19 - Learning Quality

Goals:

- stronger Learning Quality Gate;
- exploit accepted/rejected/ignored feedback;
- measure suggestion quality;
- controlled catalog publication design.

---

## v3.20 - External Skill and Occupation Knowledge

Research candidates:

- ESCO;
- ROME;
- O*NET;
- other maintained occupation/skill taxonomies.

Goals:

- reduce manual catalog maintenance;
- stable identifiers;
- multilingual labels;
- mapping to internal JobAgent concepts.

No external taxonomy should be integrated before its licensing, data model and update strategy are reviewed.

---

## v3.21 - Architecture Consolidation

Candidate goals:

- reduce duplicated skill catalogs;
- reduce duplicated models;
- move Career Workspace orchestration into services;
- strengthen user-isolated persistence;
- align ProviderSelector with actual provider execution.

---

## v4 - Intelligent JobAgent

Long-term direction:

- continuously improving market knowledge;
- explainable job recommendations;
- candidate skill-gap analysis;
- learning recommendations;
- controlled autonomous enrichment;
- multi-domain career intelligence.