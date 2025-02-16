import pytest
import time
from app.ai_logic.dispatch import dispatch_logic, UNHANDLED_EMERGENCIES
from app.schemas import EmergencySchema, ResourceSchema

def test_dispatch_simple():
    """
    Basic test to ensure a resource is assigned to an emergency.
    """
    UNHANDLED_EMERGENCIES.clear()

    now = int(time.time())

    emergencies = [
        EmergencySchema(id=1, location=(10.0, 5.0), severity=2.0, timestamp=now, type="fire")
    ]
    resources = [
        ResourceSchema(id=100, location=(0.0, 0.0), status="available", type="fire_unit"),
        ResourceSchema(id=101, location=(5.0, 5.0), status="available", type="fire_unit"),  # Additional fire unit
        ResourceSchema(id=102, location=(5.0, 5.0), status="available", type="police_unit")  # Required police unit
    ]

    assignments = dispatch_logic(emergencies, resources)

    assert len(assignments) == 3  # Two fire units and one police unit required
    assigned_resource_ids = {a["resource_id"] for a in assignments}
    assert 100 in assigned_resource_ids
    assert 101 in assigned_resource_ids
    assert 102 in assigned_resource_ids


def test_dispatch_with_queue():
    """
    Tests that unhandled emergencies are reattempted in the next dispatch cycle.
    """
    UNHANDLED_EMERGENCIES.clear()

    now = int(time.time())

    # Emergency with no available resources
    emergencies = [
        EmergencySchema(id=2, location=(20.0, 15.0), severity=5.0, timestamp=now - 50, type="fire")
    ]
    resources = []  # No resources at first

    dispatch_logic(emergencies, resources)

    # Ensure the emergency was added to the unhandled queue
    assert len(UNHANDLED_EMERGENCIES) == 1

    # Now make required resources available and re-dispatch
    resources = [
        ResourceSchema(id=200, location=(15.0, 15.0), status="available", type="fire_unit"),
        ResourceSchema(id=201, location=(18.0, 12.0), status="available", type="fire_unit"),  # Second fire unit
        ResourceSchema(id=202, location=(20.0, 15.0), status="available", type="police_unit")  # Required police unit
    ]

    assignments = dispatch_logic([], resources)  # No new emergencies, just retry the queue

    # The previous emergency should now be handled
    assert len(assignments) == 3
    assigned_resource_ids = {a["resource_id"] for a in assignments}
    assert 200 in assigned_resource_ids
    assert 201 in assigned_resource_ids
    assert 202 in assigned_resource_ids

    # Queue should now be empty
    assert len(UNHANDLED_EMERGENCIES) == 0


def test_priority_order():
    """
    Ensures higher severity and older emergencies are assigned first.
    """
    UNHANDLED_EMERGENCIES.clear()

    now = int(time.time())

    emergencies = [
        EmergencySchema(id=3, location=(5.0, 5.0), severity=3.0, timestamp=now - 30, type="fire"),
        EmergencySchema(id=4, location=(5.0, 5.0), severity=5.0, timestamp=now - 10, type="fire"),  # Highest severity
        EmergencySchema(id=5, location=(5.0, 5.0), severity=3.0, timestamp=now - 100, type="fire"),  # Oldest emergency
    ]
    resources = [
        ResourceSchema(id=300, location=(0.0, 0.0), status="available", type="fire_unit"),
        ResourceSchema(id=301, location=(10.0, 10.0), status="available", type="fire_unit"),
        ResourceSchema(id=302, location=(5.0, 5.0), status="available", type="police_unit")  # Ensure correct requirements
    ]

    assignments = dispatch_logic(emergencies, resources)

    # Ensure the highest severity emergency (ID 4) is handled first
    assert len(assignments) == 3
    assert assignments[0]["emergency_id"] == 4  # Highest severity gets priority
    assigned_resource_ids = {a["resource_id"] for a in assignments}
    assert 300 in assigned_resource_ids
    assert 301 in assigned_resource_ids
    assert 302 in assigned_resource_ids


def test_multiple_unhandled_redispatch():
    """
    Tests that multiple unhandled emergencies are correctly retried when resources free up.
    """
    UNHANDLED_EMERGENCIES.clear()

    now = int(time.time())

    # Create three emergencies but no resources
    emergencies = [
        EmergencySchema(id=6, location=(30.0, 30.0), severity=4.0, timestamp=now - 40, type="fire"),
        EmergencySchema(id=7, location=(25.0, 25.0), severity=2.0, timestamp=now - 60, type="fire"),
        EmergencySchema(id=8, location=(40.0, 40.0), severity=5.0, timestamp=now - 20, type="fire"),  # Highest severity
    ]
    resources = []  # No resources at first

    dispatch_logic(emergencies, resources)

    # All should be queued
    assert len(UNHANDLED_EMERGENCIES) == 3

    # Make enough resources available
    resources = [
        ResourceSchema(id=400, location=(30.0, 30.0), status="available", type="fire_unit"),
        ResourceSchema(id=401, location=(20.0, 20.0), status="available", type="fire_unit"),
        ResourceSchema(id=402, location=(25.0, 25.0), status="available", type="police_unit")
    ]

    assignments = dispatch_logic([], resources)  # No new emergencies

    # Ensure highest severity (ID 8) was handled first
    assert len(assignments) == 3
    assert assignments[0]["emergency_id"] == 8  # Severity 5 must be first
    assigned_resource_ids = {a["resource_id"] for a in assignments}
    assert 400 in assigned_resource_ids
    assert 401 in assigned_resource_ids
    assert 402 in assigned_resource_ids

    # Remaining emergencies should still be in queue
    assert len(UNHANDLED_EMERGENCIES) == 2
