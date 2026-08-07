
# JobAgent Development Rules

## 1. Purpose

This document defines the development rules that apply to JobAgent.

These rules are mandatory for:

- human contributors;
- Codex;
- other AI development agents;
- automated development workflows.

The goal is to preserve:

- code quality;
- maintainability;
- testability;
- backward compatibility;
- explainability;
- user-data isolation;
- predictable Git history.

The rules in this file apply unless a sprint specification explicitly overrides them.

---

## 2. General development principles

JobAgent code must be:

- readable;
- typed;
- testable;
- deterministic where reasonably possible;
- explicit about business decisions;
- explicit about failures;
- compatible with existing persisted data unless a migration is intentionally designed.

Prefer simple and explicit code over clever abstractions.

Do not optimize prematurely.

Do not introduce architecture merely for theoretical purity.

Every abstraction must solve a concrete problem.

---

## 3. Python compatibility

The project currently targets Python 3.13.

New code must remain compatible with Python 3.13.

Use:

```python
from __future__ import annotations

when consistent with the surrounding module.

Prefer:

explicit type hints;
dataclass for immutable or structured value objects;
Enum for controlled finite states;
Path instead of manual filesystem string manipulation.

Avoid unnecessary dependencies.

Do not introduce a package when the Python standard library already provides a clear solution.

4. Code style

Follow the style already established in the surrounding module.

Prioritize readability.

Functions should have one primary responsibility.

Methods should remain reasonably short.

Avoid deeply nested conditions when early returns make the flow clearer.

Prefer meaningful names over comments that merely repeat the code.

Comments should explain:

why something exists;
a non-obvious constraint;
compatibility behavior;
important business reasoning.

Comments should not explain obvious syntax.


## Business Logic

4bis. Business rules must remain explicit.

Do not introduce unexplained thresholds, hidden constants or implicit heuristics.

Prefer:

- typed business models;
- documented algorithms;
- explicit catalogs;
- named constants.

Avoid code such as:

if score > 27:

unless this threshold is explicitly documented as a business rule.

Business decisions should remain understandable by future developers and AI agents.

 
## Root Cause First

4ter. Do not fix symptoms before identifying the root cause.

When a test fails:

1. understand why;
2. inspect related modules;
3. inspect existing tests;
4. identify the real cause;
5. implement the smallest coherent fix.

Avoid introducing compatibility code that hides an architectural issue.

Document follow-up work when the root cause cannot be fully addressed within the sprint.
5. Type safety

Public functions and service methods should use type annotations.

New models should expose clear contracts.

Avoid passing unstructured dictionaries between layers when a small typed model would make the contract clearer.

When dictionaries are required for compatibility or serialization, document their expected structure.

Do not use Any unless there is a real integration or compatibility reason.

6. Dependency injection

Prefer dependency injection over hidden dependency construction.

Example:

Preferred:

class MyService:
    def __init__(
        self,
        repository: MyRepository,
    ) -> None:
        self.repository = repository

Avoid constructing lower-level infrastructure deep inside business logic unless the existing architecture explicitly expects a default dependency.

Default dependencies are acceptable when they preserve ease of use, but tests must be able to inject fakes or mocks.

7. Module responsibilities

Respect module boundaries.

src/workspace

Responsibilities:

application-level orchestration;
user-context binding;
façade services;
translation of lower-level errors.

Must not duplicate domain logic.

src/career

Responsibilities:

career analysis;
role detection;
profile generation;
provider recommendation;
Career search workflow;
career relevance filtering.
src/learning

Responsibilities:

learning observations;
candidate suggestions;
Quality Gate;
human-reviewed suggestion lifecycle.

Must not automatically mutate production reference catalogs unless a dedicated controlled publication workflow exists.

src/market

Responsibilities:

market statistics;
skill frequencies;
skill gaps;
market portrait.

Must distinguish collected-market data from Career-relevant data when both are exposed.

src/matching

Responsibilities:

profile/job matching;
exact matching;
semantic matching;
score computation;
matching explanation.
src/analysis

Responsibilities:

structured candidate/job analysis;
multidimensional analysis;
comparative scoring.
src/ai

Responsibilities:

shared skill extraction;
skill normalization;
synonym knowledge;
AI helpers;
semantic utilities.

Shared knowledge should live here rather than being duplicated in downstream modules.

src/providers

Responsibilities:

external API access;
provider-specific response parsing;
provider normalization.

Provider implementations must not contain UI logic.

src/storage

Responsibilities:

persistence;
repositories;
storage paths;
database integration.
src/auth

Responsibilities:

authentication;
authorization;
user context.
src/ui and Streamlit pages

Responsibilities:

gather user input;
render state;
call application services.

Business rules should progressively move out of Streamlit pages.

8. No duplicated business knowledge

Do not create duplicate catalogs, alias maps or normalization rules if equivalent knowledge already exists.

Before introducing:

a skill dictionary;
a role catalog;
a synonym table;
a provider mapping;
a normalization helper;

search the repository first.

If multiple historical sources already exist, prefer:

consolidation;
compatibility adapters;
a shared source of truth.

Do not create a third source merely to avoid touching existing code.

9. Skills and normalization

Skill matching must be robust to normal user and provider variations.

At minimum, where appropriate:

comparisons should be case-insensitive;
accent-insensitive matching may be used;
repeated whitespace should not break matching;
PDF line breaks inside multi-word skills must be tolerated;
aliases and synonyms should resolve toward stable canonical values.

Example:

pilotage
budgétaire

must be capable of matching:

pilotage budgétaire

when handled by the relevant skill extractor or matcher.

Avoid substring false positives.

Examples that must remain protected:

go

must not match:

gouvernance

and:

sap

must not match:

sapin

Canonical values should remain stable once introduced.

10. Canonical values versus display labels

Business logic may use normalized technical values.

UI presentation may use user-friendly labels.

Do not assume these must always be identical.

Long-term architecture may distinguish:

skill_id
canonical_value
display_label

Do not perform a large migration toward this model unless a sprint explicitly requires it.

11. Matching rules

Matching changes must preserve explainability.

The engine may distinguish:

exact matches;
alias matches;
semantic/category matches;
graph matches.

Do not silently convert semantic matches into exact matches.

If semantic evidence contributes to Career relevance, expose that decision explicitly.

A positive global score alone must not automatically make an offer career-relevant.

Career relevance must still include meaningful business evidence such as:

title match;
exact skill evidence;
semantic skill evidence.

This protects against unrelated offers receiving positive scores from:

location;
remote compatibility;
salary.
12. Score compatibility

Avoid changing scoring weights casually.

Before changing scoring:

inspect current scorer behavior;
inspect tests;
identify the functional failure;
prove that filtering or normalization is not the actual root cause.

Score-weight changes should normally have their own sprint or explicit acceptance criteria.

13. Career role context

When a profile is created from Career analysis, its selected role is meaningful application context.

Do not silently lose this context between:

CV analysis;
profile creation;
persistence;
Workspace loading;
Career search.

Before adding new persistent fields, inspect existing metadata mechanisms.

Prefer reuse of existing metadata structures when suitable.

Any new persistent role metadata must:

remain backward compatible;
allow old profiles without role metadata to load;
avoid forcing migration during unrelated sprints.

Do not migrate existing user profiles unless the sprint explicitly requests it.

14. Workspace and user isolation

Workspace features must respect the authenticated user context.

New persistent data must use the correct user-specific storage root.

Typical structure:

data/users/<user_id>/

Do not accidentally use global storage for a Workspace feature.

Before writing a new file or database:

inspect UserStoragePaths;
inspect existing repositories;
confirm the correct user-specific location.
15. Providers

External provider APIs are unreliable by nature.

Never assume:

HTTP 200;
valid JSON;
correct content type;
complete fields;
stable schemas;
non-empty responses.

Provider code should validate at least:

response status;
payload structure;
required fields.

When appropriate, validate content type before JSON decoding.

Provider errors must be isolated.

One provider failure must not destroy valid results from another provider.

Example:

France Travail failure
+
RemoteOK success

should still return RemoteOK results while clearly exposing that the search was partial.

16. Partial search results

When provider collection is partial, do not present the result as fully representative without exposing the limitation.

Relevant application models should preserve enough information to explain:

successful providers;
failed providers;
collected counts;
provider errors.

Market analysis built from partial providers should be identifiable as partial where appropriate.

17. Error handling

Do not silently swallow exceptions.

Avoid:

except Exception:
    pass

unless there is an exceptional and documented reason.

Application services may translate lower-level failures.

Use exception chaining:

raise WorkspaceError(
    "User-facing explanation."
) from error

Preserve useful diagnostic context.

Avoid leaking secrets or credentials into user-facing errors.

18. Persistence

Persistence changes must be backward compatible unless migration is an explicit sprint objective.

Before changing persisted JSON or database structure:

identify current readers;
identify current writers;
inspect tests;
determine how old data will behave.

Prefer atomic JSON writes where state consistency matters.

Do not write outside intended application or user storage roots.

Do not silently delete unknown persisted fields unless explicitly required.

19. Streamlit rules

Streamlit reruns can easily produce stale or inconsistent state.

When an action changes persistent data:

persist the change;
refresh application state;
update relevant st.session_state;
rerun only when appropriate.

Avoid displaying old cached objects after a write.

Buttons must have stable and unique keys.

Do not place irreversible business logic only inside rendering functions.

20. Session state

Treat st.session_state as UI/application state, not as a replacement for persistence.

Persistent domain state must live in repositories or appropriate storage.

Use session state for:

selected UI state;
cached application results;
rerun coordination.

Document non-obvious session-state keys.

21. Learning Engine safety

Learning is human-assisted.

Current statuses include:

candidate;
accepted;
rejected;
ignored.

Human decisions should be persisted.

Accepted does not mean automatically published into production taxonomies.

Rejected and ignored decisions may later contribute to Learning Quality, but such behavior must be explicit and tested.

Avoid feedback loops where noisy suggestions automatically create more noisy knowledge.

22. Learning Quality Gate

Quality Gate rules must remain explainable.

If dynamic feedback is introduced later, preserve:

static safety rules;
deterministic fallbacks;
auditability.

Never allow user feedback alone to bypass mandatory static quality constraints.

23. Market Analyzer

Market analysis should clearly define its input population.

Possible populations include:

all collected jobs;
deduplicated jobs;
Career-relevant jobs.

Do not mix these concepts without explicit naming.

If the UI displays:

126 jobs analyzed
0 relevant jobs

the underlying result model should make it possible to explain why.

24. Search diagnostics

Career filtering should be diagnosable.

Avoid production print() statements.

Prefer structured diagnostics.

Useful diagnostic fields may include:

job identity;
score;
title match;
exact match count;
semantic match count;
relevance evidence count;
accepted/rejected;
rejection reason.

Rejection reasons should use stable, machine-readable values where appropriate.

Examples:

zero_score
insufficient_relevance_evidence

Diagnostics should live in Career/search result models rather than polluting the canonical Job model unless there is a strong reason.

25. UI changes

Do not redesign UI during a backend-quality sprint unless the sprint explicitly requests UI changes.

Keep functional and visual scope separate when possible.

Small diagnostic displays may be acceptable if explicitly included in acceptance criteria.

26. Tests are mandatory

Every behavior change requires tests.

Before adding a new test:

inspect existing test organization;
reuse existing helpers/fakes when appropriate;
avoid duplicate test infrastructure.

Tests should be deterministic.

Do not require live external APIs for the standard unit suite.

Prefer:

fake providers;
temporary directories;
in-memory or isolated repositories;
explicit fixtures;
deterministic sample payloads.
27. Test hierarchy

For each sprint, run tests progressively.

Level 1 — targeted tests

Tests directly covering modified components.

Level 2 — dependent module tests

Tests for services consuming the changed component.

Level 3 — complete unit suite

When reasonably possible:

python -m unittest discover \
  -s tests \
  -p "test_*.py"

If the repository contains pytest-style tests not discovered by unittest and pytest is installed, also use the appropriate pytest command.

Never claim:

all tests pass

unless the relevant complete suite was actually executed.

28. Functional tests

Unit tests are not a substitute for functional validation.

The Product Owner performs functional validation for:

Streamlit behavior;
real CV files;
actual provider integrations;
authentication;
user experience;
real persisted user data.

AI development agents must provide explicit functional-validation instructions at sprint completion.

Do not mark functional validation as complete yourself unless it was actually performed.

29. Regression policy

Existing passing tests must remain passing unless:

the sprint intentionally changes the expected behavior;
tests are updated with clear justification.

Do not modify a failing test merely to make the suite green without proving the new expected behavior is correct.

When a test exposes an implementation detail rather than intended behavior, explain that before changing it.

30. Test doubles

Fakes and mocks are useful for deterministic tests.

However, distinguish clearly between:

unit tests using a fake dependency;
integration tests using the real component.

Example:

A FakeSkillExtractor should not be used to validate actual Finance extraction behavior.

Integration behavior should instantiate the real extractor where necessary.

31. Refactoring policy

A sprint should primarily solve its declared problem.

Do not combine unrelated cleanup.

Avoid massive refactors during focused feature sprints.

Allowed opportunistic cleanup should be:

local;
low risk;
directly related to the touched code.

If a larger architectural issue is discovered, document it as follow-up work.

32. Legacy compatibility

The historical app.py flow still exists.

Do not break it casually.

The preferred architectural direction is Workspace, but migration must be incremental.

Any sprint affecting shared services must consider both:

historical app flow;
Career Workspace flow.
33. Model duplication

The repository currently contains some overlapping concepts and models.

Do not introduce additional duplicates.

Before creating a new model:

search the repository;
inspect similar existing models;
decide whether extension or reuse is preferable.

Do not perform a full consolidation unless explicitly scoped.

34. Documentation

When behavior changes materially, update relevant documentation.

Documentation should describe current implementation, not only architecture aspirations.

Avoid documenting components as operational if they are not actually wired into production paths.

35. Git branch policy

One sprint uses one feature branch.

Branch format:

feature/vX.Y.Z-short-description

Example:

feature/v3.18.2-search-quality

Do not switch branch during the sprint unless explicitly requested.

Do not work directly on develop.

36. Git commit policy

Do not commit unless the Product Owner or sprint instructions explicitly authorize it.

Before committing:

tests must be green;
inspect git status;
inspect git diff;
ensure no unrelated files are included.

Commit messages should be concise and descriptive.

Recommended pattern:

feat: improve career search relevance diagnostics

or:

fix: align finance skill aliases in job matching

Avoid meaningless messages such as:

update files
fix stuff
changes
37. Untracked files

Do not delete or overwrite unrelated untracked files.

Before broad Git operations, inspect:

git status

Governance documents, sprint specifications and local developer files may be intentionally untracked during preparation.

Preserve them unless explicitly asked otherwise.

38. No force operations by default

Do not use:

git reset --hard
git clean -fd
git push --force

unless explicitly authorized.

Do not rewrite shared history casually.

39. Security

Never commit:

passwords;
API keys;
OAuth secrets;
tokens;
private credentials;
user CV data;
private user information.

Respect .gitignore.

Do not print secrets in logs or test output.

40. External APIs

Do not add live API dependencies to unit tests.

Use recorded/synthetic payloads where needed.

Integration with external providers should have:

deterministic parsing tests;
explicit error tests;
separate functional validation.
41. Performance

Do not optimize without evidence.

However, avoid obvious unnecessary repeated work in Streamlit reruns.

Caching may be used when:

results are safe to cache;
cache invalidation is understood;
user isolation is preserved.

Never cache one user’s private state into another user’s context.

42. Backward-compatible defaults

When extending dataclasses or result models, prefer default values where this preserves existing callers.

Example:

@dataclass
class SearchResult:
    jobs: list[Job]
    diagnostics: tuple[Diagnostic, ...] = ()

Avoid forcing unrelated callers to change without functional reason.

43. Serialization

Any object stored in:

JSON;
session state;
database fields;
Job.match_details;

must remain safely serializable.

Use existing serialization helpers when available.

Do not place arbitrary complex runtime objects into persisted structures.

44. Structured diagnostics

Diagnostic models should favor stable fields over preformatted human text.

Preferred:

reason="zero_score"

with presentation translating it later.

Avoid embedding business logic only in French display strings.


## Code Review

44 bis. Before considering a sprint complete, perform a complete review.

Verify:

- architecture consistency;
- backward compatibility;
- duplicated business knowledge;
- unintended side effects;
- unnecessary complexity;
- modified tests;
- Git diff.

The objective is not only to make tests pass, but to ensure the implementation remains coherent with the architecture.


45. Definition of Done

A development task is complete only when:

implementation is complete;
required tests were added or updated;
targeted tests pass;
dependent tests pass;
full available suite was run when practical;
no known regression is hidden;
Git diff was reviewed;
functional validation instructions are documented;
known risks are listed.
46. Sprint completion report

At the end of every sprint, the development agent must report:

Summary

What changed and why.

Files modified

Exact list of created, modified or deleted files.

Technical decisions

Important design decisions and compatibility choices.

Tests executed

Exact commands.

Example:

python -m unittest \
  tests.test_career_search_workflow \
  -v

Include result counts when available.

Full-suite status

Clearly state whether the full suite was run.

Git status

Provide the relevant result of:

git status
Diff summary

Provide:

git diff --stat
Risks and follow-up

List remaining known issues.

Functional validation

Provide exact local steps for Product Owner validation.

Recommended commit message

Provide one suggested commit message.

Do not commit automatically unless explicitly authorized.

47. AI agent workflow

Before coding:

read AGENTS.md;
read ARCHITECTURE.md;
read this file;
read the active sprint specification;
inspect affected code;
inspect existing tests;
produce a short implementation plan.

During coding:

make the smallest coherent change;
add tests;
run tests incrementally;
inspect failures;
fix root causes rather than masking failures.

After coding:

run targeted tests;
run dependent tests;
run the full available suite;
inspect Git status;
inspect the diff;
produce the completion report.
48. Principle of least surprise

A user, developer or future AI agent reading JobAgent code should be able to understand:

why an offer matched;
why an offer was rejected;
why a Learning suggestion exists;
where user data is stored;
which provider failed;
which role was selected.

Prefer architecture that makes these decisions visible and traceable.

49. Final rule

When uncertain between:

a fast workaround;
a slightly slower but coherent solution;

prefer the coherent solution if it stays within sprint scope.

Do not hide architectural debt.

Document it and schedule it when fixing it would exceed the current sprint.