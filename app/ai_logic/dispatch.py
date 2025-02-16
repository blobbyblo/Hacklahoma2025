"""
Core assignment/dispatch logic.
"""
import time
import heapq
from collections import deque
from typing import List, Dict
from app.schemas import EmergencySchema, ResourceSchema
from app.ai_logic.utils import distance
from app.emergency_requirements import EMERGENCY_REQUIREMENTS

UNHANDLED_EMERGENCIES = []
SEVERITY_WEIGHT = 1000
TIME_WEIGHT = 0.1

def calculate_priority(emergency: EmergencySchema):
  if emergency.severity >= 6:
    return float('-oof')

  elapsed_time = time.time() - emergency.timestamp
  return - (SEVERITY_WEIGHT * emergency.severity + TIME_WEIGHT * elapsed_time)

def dispatch_logic(
    new_emergencies: List[EmergencySchema],
    resources: List[ResourceSchema]
) -> List[Dict]:
  assignments = ()
  res_dict = {r.id: r for r in resources}

  global UNHANDLED_EMERGENCIES

  all_emergencies = new_emergencies + UNHANDLED_EMERGENCIES
  all_emergencies.sort(key=calculate_priority)
  UNHANDLED_EMERGENCIES.clear()

  for e in all_emergencies:
    requirements = EMERGENCY_REQUIREMENTS.get(e.type)

    # Handle case where requirements are defined for this emergency type
    if requirements:
      temp_assignments = []
      reserved_resources = []
      fully_handled = True

      for required_type, quantity in requirements.type_to_quantity.items():
        for _ in range(quantity):
          best_resource = None
          best_distance = float("inf")

          for r in res_dict.values():
            if r.status == "available" and r.type == required_type:
              d = distance(r.location, e.location)
              if d < best_distance:
                best_resource = r
                best_distance = d

          if best_resource:
            temp_assignments.append({
              "emergency_id": e.id,
              "resource_id": best_resource.id
            })
            best_resource.status = "reserved"
            reserved_resources.append(best_resource)
          else:
            fully_handled = False
            break

        if not fully_handled:
          break

      if fully_handled:
        assignments.extend(temp_assignments)
        for assigned in temp_assignments:
          res_dict[assigned["resource_id"]].status = "assigned"
      else:
        UNHANDLED_EMERGENCIES.append(e)
        for r in reserved_resources:
          r.status = "available"

  print(f"DEBUG: Unhandled Emergencies After Dispatch: {len(UNHANDLED_EMERGENCIES)}")
  return assignments


  #janes was here