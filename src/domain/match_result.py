from dataclasses import dataclass, field


@dataclass
class MatchResult:
    score: int
    matched_skills: list[str]
    missing_skills: list[str]
    details: dict = field(default_factory=dict)