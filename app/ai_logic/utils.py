"""
Helper functions for AI logic.
"""
import math
from app.schemas import EmergencySchema, ResourceSchema

def distance(loc1, loc2):
  return math.sqrt((loc1[0] - loc2[0])**2 + (loc1[1] - loc2[1])**2)

def resource_can_handle(resource: ResourceSchema, emergency: EmergencySchema):
  if resource.type == "fire_unit" and emergency.type == "fire":
    return True
  if resource.type == "police_unit" and emergency.type == "police":
    return True
  if resource.type == "ems_unit" and emergency.type == "medical":
    return True
  return False