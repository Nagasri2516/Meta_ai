from pydantic import BaseModel
from typing import List


class Bin(BaseModel):
    pos: List[int]
    fill: float
    priority: int


class SmartWasteObservation(BaseModel):
    truck_position: List[int]
    bins: List[Bin]
    fuel: int


class SmartWasteAction(BaseModel):
    action_type: str
    direction: str | None = None