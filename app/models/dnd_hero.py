# app/models/dnd_hero.py

from pydantic import BaseModel
from typing import List, Optional
from app.models.ability_scores import AbilityScores
from app.models.equipment import Equipment
from app.models.skill_proficiencies import SkillProficiencies
from app.models.spell import Spell


class DnDHero(BaseModel):
    id: str
    name: str
    race: str
    class_: str  # Avoids conflict with the Python `class` keyword
    level: int
    background: Optional[str] = None
    alignment: Optional[str] = None

    # Nested fields
    ability_scores: AbilityScores
    skill_proficiencies: SkillProficiencies
    equipment: Equipment
    spells: Optional[List[Spell]] = None  # Optional, only for spellcasters

    hit_points: int
    armor_class: int
    speed: int

    # Additional optional features
    personality_traits: Optional[str] = None
    ideals: Optional[str] = None
    bonds: Optional[str] = None
    flaws: Optional[str] = None
