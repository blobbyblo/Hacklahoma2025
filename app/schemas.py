"""
Shapes for FastAPI schemas.
"""
from pydantic import BaseModel, validator
from typing import Tuple, Optional

class EmergencySchema(BaseModel):
  id: int
  location: Tuple[float, float]
  severity: float
  timestamp: int
  type: str

class ResourceSchema(BaseModel):
  id: int
  location: Tuple[float, float]
  status: str
  type: str
