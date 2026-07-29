from dataclasses import dataclass

@dataclass
class JobOffer:
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str

    salary: str = ""
    contract: str = ""
    remote: bool = False