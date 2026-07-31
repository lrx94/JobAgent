import unittest

from src.profile import Profile
from src.search_request import SearchRequest


class TestSearchRequest(unittest.TestCase):

    def test_builds_request_from_profile(self):
        profile = Profile(
            name="Data Engineer",
            keywords=[
                "Python",
                "SQL",
            ],
            locations=[
                "Paris",
                "Remote",
            ],
            salary_min=65000,
            remote=True,
        )

        request = SearchRequest.from_profile(
            profile
        )

        self.assertEqual(
            request.keywords,
            ["Python", "SQL"],
        )
        self.assertEqual(
            request.locations,
            ["Paris", "Remote"],
        )
        self.assertEqual(
            request.salary_min,
            65000,
        )
        self.assertTrue(request.remote)

    def test_primary_values(self):
        request = SearchRequest(
            keywords=["Python", "Azure"],
            locations=["Paris"],
        )

        self.assertEqual(
            request.primary_keyword,
            "Python",
        )
        self.assertEqual(
            request.primary_location,
            "Paris",
        )

    def test_page_size_is_limited(self):
        request = SearchRequest(
            page=0,
            page_size=500,
        )

        self.assertEqual(request.page, 1)
        self.assertEqual(
            request.page_size,
            100,
        )

    def test_values_are_deduplicated(self):
        request = SearchRequest(
            keywords=[
                "Python",
                " python ",
                "SQL",
            ],
        )

        self.assertEqual(
            request.keywords,
            ["Python", "SQL"],
        )


if __name__ == "__main__":
    unittest.main()