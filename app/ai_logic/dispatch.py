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
    return float('-inf')

  elapsed_time = time.time() - emergency.timestamp
  return - (SEVERITY_WEIGHT * emergency.severity + TIME_WEIGHT * elapsed_time)

def dispatch_logic(
    new_emergencies: List[EmergencySchema],
    resources: List[ResourceSchema]
) -> List[Dict]:
  print("=== Starting dispatch_logic ===")
  assignments = []
  res_dict = {r.id: r for r in resources}
  print(f"DEBUG: Resources received: {len(resources)}")
  print("DEBUG: Resource IDs and statuses:")
  for rid, res in res_dict.items():
    print(f"   ID: {rid}, Type: {res.type}, Status: {res.status}, Location: {res.location}")

  global UNHANDLED_EMERGENCIES

  print(f"DEBUG: new_emergencies received: {len(new_emergencies)}")
  for e in new_emergencies:
    print(
      f"   Emergency ID: {e.id}, Type: {e.type}, Severity: {e.severity}, Timestamp: {e.timestamp}, Location: {e.location}")

  # Combine new emergencies with unhandled ones
  all_emergencies = new_emergencies + UNHANDLED_EMERGENCIES
  print(f"DEBUG: Combined emergencies count (new + unhandled): {len(all_emergencies)}")

  # Sort emergencies by priority
  all_emergencies.sort(key=calculate_priority)
  print("DEBUG: Emergencies sorted by priority:")
  for e in all_emergencies:
    priority = calculate_priority(e)
    print(f"   Emergency ID: {e.id} has priority: {priority}")

  # Clear the unhandled emergencies list
  UNHANDLED_EMERGENCIES.clear()
  print("DEBUG: Cleared UNHANDLED_EMERGENCIES.")

  # Process each emergency in order of priority
  for e in all_emergencies:
    print(f"DEBUG: Processing Emergency ID: {e.id}, Type: {e.type}")
    requirements = EMERGENCY_REQUIREMENTS.get(e.type)
    if requirements:
      print(f"   Requirements found for type '{e.type}': {requirements.type_to_quantity}")
      temp_assignments = []
      reserved_resources = []
      fully_handled = True

      for required_type, quantity in requirements.type_to_quantity.items():
        print(f"   Need {quantity} resource(s) of type '{required_type}' for Emergency ID: {e.id}")
        for i in range(quantity):
          best_resource = None
          best_distance = float("inf")
          # Find the closest available resource for this requirement
          for r in res_dict.values():
            if r.status == "available" and r.type == required_type:
              d = distance(r.location, e.location)
              print(f"      Checking resource ID: {r.id} of type '{r.type}' at {r.location} -> distance: {d}")
              if d < best_distance:
                best_resource = r
                best_distance = d
          if best_resource:
            print(
              f"      Best resource for required type '{required_type}' is resource ID: {best_resource.id} at distance {best_distance}")
            temp_assignments.append({
              "emergency_id": e.id,
              "resource_id": best_resource.id,
              "emergency_location": e.location
            })
            best_resource.status = "reserved"
            reserved_resources.append(best_resource)
          else:
            print(f"      No available resource found for required type '{required_type}' for Emergency ID: {e.id}")
            fully_handled = False
            break

        if not fully_handled:
          print(
            f"   Could not fully handle Emergency ID: {e.id} due to missing resource(s) of required type '{required_type}'.")
          break

      if fully_handled:
        print(f"DEBUG: Fully handled Emergency ID: {e.id} with assignments: {temp_assignments}")
        assignments.extend(temp_assignments)
        # Mark the reserved resources as assigned
        for assigned in temp_assignments:
          res_dict[assigned["resource_id"]].status = "assigned"
          print(f"   Resource ID: {assigned['resource_id']} set to 'assigned'")
      else:
        print(f"DEBUG: Emergency ID: {e.id} is unhandled. Returning reserved resources to available.")
        UNHANDLED_EMERGENCIES.append(e)
        for r in reserved_resources:
          r.status = "available"
          print(f"   Resource ID: {r.id} reset to 'available'")
    else:
      print(f"DEBUG: No requirements found for Emergency ID: {e.id} of type '{e.type}'. Skipping assignment.")

  print(f"DEBUG: Unhandled Emergencies After Dispatch: {len(UNHANDLED_EMERGENCIES)}")
  print(f"=== dispatch_logic complete: {len(assignments)} assignments generated ===")
  return assignments
