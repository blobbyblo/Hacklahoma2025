"""
Quick training dummy data.
"""

DUMMY_EMERGENCIES = [
  {"id": 1, "location": (10.0, 5.0), "severity": 2.0, "type": "fire"},
  {"id": 2, "location": (25.0, 2.0), "severity": 1.0, "type": "police"},
  {"id": 2, "location": (12.0, 8.0), "severity": 3.0, "type": "medical"},
]

DUMMY_RESOURCES = [
    {"id": 100, "location": (0.0, 0.0), "status": "available", "type": "fire_unit"},
    {"id": 101, "location": (5.0, 5.0), "status": "available", "type": "ems_unit"},
    {"id": 102, "location": (10.0, 10.0), "status": "available", "type": "police_unit"}
]
