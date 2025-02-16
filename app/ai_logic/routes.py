"""
FastAPI routes that handle dispatch/AI endpoints.
"""
import asyncio

from fastapi import APIRouter
from typing import List
from app.schemas import EmergencySchema, ResourceSchema
from app.ai_logic.dispatch import dispatch_logic

router = APIRouter()

ACTIVE_EMERGENCIES = []
RESOURCES = []

@router.post("/emergencies")
def add_emergency(emergencies: List[EmergencySchema]):
  """
  Endpoint to add or update emergencies in memory.
  """
  global ACTIVE_EMERGENCIES
  ACTIVE_EMERGENCIES.append(emergencies)
  print(f"DEBUG: Emergencies updated: {len(emergencies)}")
  return {"message": "Emergencies received.", "count": len(emergencies)}

@router.post("/resources")
def update_resources(resources: List[ResourceSchema]):
  """
  Endpoint to update resources in memory.
  """
  global RESOURCES
  RESOURCES = resources
  print(f"DEBUG: DResources updated: {len(resources)}")
  return {"message": "Resources updated.", "count": len(resources)}

@router.post("/dispatch")
def do_dispatch():
  """
  Calls dispatch logic and returns assignments.
  """
  global ACTIVE_EMERGENCIES, RESOURCES
  assignments = dispatch_logic(ACTIVE_EMERGENCIES, RESOURCES)
  print(f"DEBUG: Dispatch assignments: {len(assignments)}")
  return {"assignments": assignments}

@router.post("/ping")
def is_alive():
  """
  Alive check.
  """
  return {"message": "Yes"}
