from pydantic import BaseModel
from typing import List, Optional


class SmartWasteAction(BaseModel):
    action_type: str
    direction: Optional[str] = None


class Bin(BaseModel):
    pos: List[int]
    fill: float
    priority: int


class SmartWasteObservation(BaseModel):
    truck_position: List[int]
    bins: List[Bin]
    fuel: int
    reward: float
    done: bool