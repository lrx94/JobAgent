from dataclasses import dataclass, field


@dataclass
class MatchResult:
    score: int
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)