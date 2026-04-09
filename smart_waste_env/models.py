# smart_waste_env/models.py
from pydantic import BaseModel
from typing import List, Optional

class Bin(BaseModel):
    pos: List[int]
    fill: float
    priority: Optional[int] = 1

class SmartWasteObservation(BaseModel):
    truck_position: List[int]
    bins: List[Bin]
    fuel: int

class SmartWasteAction(BaseModel):
    action_type: str
    direction: Optional[str] = None