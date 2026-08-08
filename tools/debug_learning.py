from pathlib import Path
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.auth.models import UserContext
from src.workspace import build_workspace

from src.workspace.search import (
    WorkspaceSearchService,
)

STORAGE_ROOT = (
    Path("data")
    / "users"
)

# ------------------------------------------------------------------

USER_ID = "268e703e-c19a-5e25-8bbe-91756e692fe7"
PROFILE_ID = "dsi_cio"

# ------------------------------------------------------------------

workspace = build_workspace(
    user_context=UserContext(
        user_id=USER_ID,
        display_name="Debug",
    ),
    storage_root=STORAGE_ROOT,
)

search_service = WorkspaceSearchService(
    profile_service=workspace.profile_service,
)

print("=" * 80)
print("Recherche des offres...")
print("=" * 80)

result = search_service.search(
    PROFILE_ID
)

jobs = tuple(
    result.jobs
)

print(f"{len(jobs)} offres récupérées")

print()
print("=" * 80)
print("Learning")
print("=" * 80)

learning = workspace.learning_service.analyze_jobs(
    jobs,
    profile_id=PROFILE_ID,
)

print()
print(f"{len(learning.stored)} suggestions")

print()

for suggestion in learning.stored[:20]:
    print(
        suggestion.term,
        suggestion.occurrence_count,
    )
