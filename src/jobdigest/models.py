from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Job:
    source: str
    id: str
    title: str
    company: str
    location: str
    is_remote: bool
    url: str
    salary: dict | None = None
    employment_type: str | None = None
    posted_date: datetime | None = None
    description: str | None = None


@dataclass
class Profile:
    title_variants: list = field(default_factory=list)
    skills: list = field(default_factory=list)
    seniority_terms: list = field(default_factory=list)
    experience_terms: list = field(default_factory=list)
    location: str = ""
    acceptable_locations: list = field(default_factory=list)
    work_types: list = field(default_factory=list)
    work_authorization: str = ""
    salary_floor: dict | None = None
    employment_types: list = field(default_factory=list)
