# client/models/equipment.py

from typing import Optional, List
from pydantic import BaseModel


class Equipment(BaseModel):
    weapon: Optional[str] = None
    armor: Optional[str] = None
    items: List[str] = []
