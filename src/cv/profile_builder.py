from src.ai import SkillExtractor
from src.domain.profile import Profile


class ProfileBuilder:

    def __init__(self):
        self.extractor = SkillExtractor()

    def build(self, text: str) -> Profile:

        skills = self.extractor.extract(text)

        return Profile(
            name="Profil importé",
            keywords=skills,
            locations=[],
            salary_min=0,
            remote=False,
        )