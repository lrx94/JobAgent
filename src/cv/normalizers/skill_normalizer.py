from dataclasses import dataclass


@dataclass(frozen=True)
class SkillAlias:
    alias: str
    canonical: str


class SkillNormalizer:
    """Normalisation des compétences."""

    _ALIASES = {
        "sqlserver": "SQL Server",
        "sql server": "SQL Server",
        "microsoft sql server": "SQL Server",
        "ms sql": "SQL Server",
        "ms sql server": "SQL Server",
        ".net": ".NET",
        "dotnet": ".NET",
        "asp.net": "ASP.NET",
        "c#": "C#",
        "js": "JavaScript",
        "javascript": "JavaScript",
        "ts": "TypeScript",
        "typescript": "TypeScript",
    }

    @classmethod
    def normalize(cls, skill: str) -> str:
        if not skill:
            return ""

        key = skill.strip().lower()
        return cls._ALIASES.get(key, skill.strip())