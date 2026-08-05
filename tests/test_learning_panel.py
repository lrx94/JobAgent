import csv
import io
import unittest
from src.learning import (
    LearningSuggestion,
    SuggestionStatus,
    SuggestionType,
)

from src.ui.learning_panel import (
    build_learning_export_csv,
)
from src.learning import (
    LearningObservationOrigin,
    LearningSuggestion,
    SuggestionStatus,
    SuggestionType,
)
class TestLearningExportCSV(
    unittest.TestCase
):

    def test_exports_learning_suggestions(
        self,
    ) -> None:
        suggestion = LearningSuggestion(
            suggestion_id="skill-sql",
            observed_term="SQL",
            normalized_term="sql",
            suggestion_type=(
                SuggestionType.SKILL
            ),
            occurrence_count=12,
            source_count=2,
            sources=(
                "france travail",
                "remoteok",
            ),
            contexts=(
                "SQL requis.",
                "Expertise SQL.",
            ),
            confidence=0.75,
            status=(
                SuggestionStatus.ACCEPTED
            ),
            origins=(
                LearningObservationOrigin
                .JOB_ANALYZER,
                LearningObservationOrigin
                .PROVIDER,
            ),
        )

        content = (
            build_learning_export_csv(
                (suggestion,)
            )
        )

        decoded = content.decode(
            "utf-8-sig"
        )

        rows = list(
            csv.DictReader(
                io.StringIO(decoded),
                delimiter=";",
            )
        )


        self.assertEqual(
            len(rows),
            1,
        )

        row = rows[0]

        self.assertEqual(
            row["terme_observe"],
            "SQL",
        )

        self.assertEqual(
            row["terme_normalise"],
            "sql",
        )

        self.assertEqual(
            row["statut"],
            SuggestionStatus.ACCEPTED.value,
        )

        self.assertEqual(
            row["occurrences"],
            "12",
        )

        self.assertEqual(
            row["nombre_sources"],
            "2",
        )

        self.assertEqual(
            row["sources"],
            "france travail | remoteok",
        )

        self.assertEqual(
            row["origines"],
            "job_analyzer | provider",
        )

    def test_empty_export_contains_header(
        self,
    ) -> None:
        content = (
            build_learning_export_csv(
                ()
            )
        )

        decoded = content.decode(
            "utf-8-sig"
        )

        rows = list(
            csv.reader(
                io.StringIO(decoded),
                delimiter=";",
            )
        )

        self.assertEqual(
            len(rows),
            1,
        )

        self.assertIn(
            "terme_normalise",
            rows[0],
        )