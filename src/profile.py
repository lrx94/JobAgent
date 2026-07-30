from dataclasses import dataclass, field


@dataclass
class Profile:

    name: str

    keywords: list[str] = field(default_factory=list)

    locations: list[str] = field(default_factory=list)

    salary_min: int = 0

    remote: bool = False