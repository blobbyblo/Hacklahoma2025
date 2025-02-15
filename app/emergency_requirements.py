from typing import Dict

class EmergencyRequirement:
  def __init__(self, type_to_quantity: Dict[str, int]):
    self.type_to_quantity = type_to_quantity

EMERGENCY_REQUIREMENTS = {
  "fire": EmergencyRequirement({
    "fire_unit": 2,
    "police_unit": 1
  }),
  "police": EmergencyRequirement({
    "police_unit": 2
  }),
  "ems": EmergencyRequirement({
    "fire_unit": 1,
    "ems_unit": 1
  })
}
