from dataclasses import dataclass, field

@dataclass
class Job:
    title: str
    company: str
    location: str
    description: str
    source: str

    url: str = ""
    salary: int = 0
    remote: bool = False

    score: int = 0

    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)

    explanation: str = ""