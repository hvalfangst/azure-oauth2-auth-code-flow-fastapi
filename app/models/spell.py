# app/models/spell.py

from typing import List
from pydantic import BaseModel


class Spell(BaseModel):
    name: str
    level: int
    casting_time: str
    range: str
    components: List[str]
    duration: str
