from dataclasses import dataclass


@dataclass(frozen=True)
class Monitor:
    name: str
    version: str
