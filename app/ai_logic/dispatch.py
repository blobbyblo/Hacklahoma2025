"""
Core assignment/dispatch logic using Google OR-Tools for optimization.
"""
import time
import heapq
from collections import deque
from typing import List, Dict
from app.schemas import EmergencySchema, ResourceSchema
from app.ai_logic.utils import distance
from app.emergency_requirements import EMERGENCY_REQUIREMENTS

from ortools.sat.python import cp_model

UNHANDLED_EMERGENCIES = []
SEVERITY_WEIGHT = 1000
TIME_WEIGHT = 0.1

# Scaling factor for converting float distances and scores to integers
SCALE = 1000
# A large constant to prioritize emergency assignment over distance cost.
BIG_VALUE = 10**8

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

    # Sort emergencies by priority (for logging purposes)
    all_emergencies.sort(key=calculate_priority)
    print("DEBUG: Emergencies sorted by priority:")
    for e in all_emergencies:
        priority = calculate_priority(e)
        print(f"   Emergency ID: {e.id} has priority: {priority}")

    # Clear the unhandled emergencies list (we will repopulate it later for those not served)
    UNHANDLED_EMERGENCIES.clear()
    print("DEBUG: Cleared UNHANDLED_EMERGENCIES.")

    # Prepare data for optimization:
    # We'll create a "task" for each required resource unit per emergency.
    # An emergency is served (y_e = 1) if and only if all its tasks are assigned.
    tasks = []  # each task is a dict with keys: 'emergency', 'required_type'
    emergency_to_tasks = {}  # mapping: emergency_id -> list of task indices

    # Only consider emergencies with defined requirements
    emergencies_with_requirements = []
    for e in all_emergencies:
        requirements = EMERGENCY_REQUIREMENTS.get(e.type)
        if not requirements:
            print(f"DEBUG: No requirements found for Emergency ID: {e.id} of type '{e.type}'. Skipping assignment.")
            continue
        emergencies_with_requirements.append(e)
        emergency_to_tasks[e.id] = []
        for req_type, quantity in requirements.type_to_quantity.items():
            print(f"DEBUG: Emergency ID: {e.id} requires {quantity} resource(s) of type '{req_type}'.")
            for _ in range(quantity):
                task = {
                    'emergency': e,
                    'required_type': req_type,
                    'emergency_location': e.location
                }
                task_idx = len(tasks)
                tasks.append(task)
                emergency_to_tasks[e.id].append(task_idx)

    # List of available resources (only those with status "available")
    available_resources = [r for r in resources if r.status == "available"]
    print(f"DEBUG: Available resources for optimization: {len(available_resources)}")

    # Build the CP-SAT model
    model = cp_model.CpModel()

    # Decision variables:
    # For each emergency (with requirements), a binary variable indicating if it is fully served.
    emergency_var = {}
    for e in emergencies_with_requirements:
        emergency_var[e.id] = model.NewBoolVar(f"serve_{e.id}")

    # For each task, for each eligible resource, create a binary variable.
    # We'll index these by (task_idx, resource_id)
    x_vars = {}
    # Also, for each task, keep track of the list of eligible resource ids.
    task_to_eligible_resources = {}

    for t_idx, task in enumerate(tasks):
        req_type = task['required_type']
        e = task['emergency']
        eligible_resources = []
        for r in available_resources:
            if r.type == req_type:
                eligible_resources.append(r.id)
                x_vars[(t_idx, r.id)] = model.NewBoolVar(f"x_{t_idx}_{r.id}")
        task_to_eligible_resources[t_idx] = eligible_resources

        # Each task must be assigned exactly if the emergency is served.
        # If the emergency is not served (y_e == 0), then no resource is assigned.
        model.Add(sum(x_vars[(t_idx, r_id)] for r_id in eligible_resources) == emergency_var[e.id])

    # A resource can be assigned to at most one task.
    for r in available_resources:
        # Collect all tasks for which resource r is eligible.
        tasks_for_resource = []
        for t_idx, eligible in task_to_eligible_resources.items():
            if r.id in eligible:
                tasks_for_resource.append(x_vars[(t_idx, r.id)])
        if tasks_for_resource:
            model.Add(sum(tasks_for_resource) <= 1)

    # Objective:
    # We want to maximize a combination of:
    #   (a) Serving high-priority emergencies (each emergency gets a score based on severity and elapsed time)
    #   (b) Minimizing the total distance from resources to emergencies.
    # We combine these terms by giving emergency scores a large multiplier.
    objective_terms = []

    # Emergency-serving term:
    for e in emergencies_with_requirements:
        elapsed_time = time.time() - e.timestamp
        # For emergencies with severity >= 6, use an extra-large score.
        if e.severity >= 6:
            score = BIG_VALUE
        else:
            score = SEVERITY_WEIGHT * e.severity + TIME_WEIGHT * elapsed_time
        # Scale score to integer.
        score_int = int(score * SCALE)
        objective_terms.append(score_int * emergency_var[e.id])

    # Distance term (to be minimized, so subtract it):
    for t_idx, task in enumerate(tasks):
        e = task['emergency']
        e_location = task['emergency_location']
        for r_id in task_to_eligible_resources[t_idx]:
            r = res_dict[r_id]
            d = distance(r.location, e_location)
            d_int = int(d * SCALE)
            # Subtract the distance cost if assigned.
            objective_terms.append(- d_int * x_vars[(t_idx, r_id)])

    model.Maximize(sum(objective_terms))

    # Solve the model
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        print("DEBUG: No feasible solution found by OR-Tools. No assignments made.")
        # If no solution, mark all emergencies as unhandled.
        for e in emergencies_with_requirements:
            UNHANDLED_EMERGENCIES.append(e)
        print(f"DEBUG: Unhandled Emergencies After Dispatch: {len(UNHANDLED_EMERGENCIES)}")
        print("=== dispatch_logic complete: 0 assignments generated ===")
        return assignments

    # Retrieve assignments:
    # For each emergency, if it is served (emergency_var == 1) then for each of its tasks, find the assigned resource.
    served_emergency_ids = set()
    for e in emergencies_with_requirements:
        if solver.Value(emergency_var[e.id]) == 1:
            served_emergency_ids.add(e.id)

    # For emergencies that are served, record the assignments.
    # Also, update the status of the resource to "assigned".
    # For tasks of emergencies that are not served, add the emergency back to UNHANDLED_EMERGENCIES.
    processed_emergencies = set()
    for t_idx, task in enumerate(tasks):
        e = task['emergency']
        if e.id not in served_emergency_ids:
            continue  # skip tasks for unserved emergencies
        # For this task, find the resource assigned (there should be exactly one)
        assigned_resource_id = None
        for r_id in task_to_eligible_resources[t_idx]:
            if solver.Value(x_vars[(t_idx, r_id)]) == 1:
                assigned_resource_id = r_id
                break
        if assigned_resource_id is not None:
            assignments.append({
                "emergency_id": e.id,
                "resource_id": assigned_resource_id,
                "emergency_location": task['emergency_location']
            })
            # Update the resource status in res_dict.
            res_dict[assigned_resource_id].status = "assigned"
        else:
            # Should not happen because the constraint ensures assignment if emergency is served.
            print(f"DEBUG: Task {t_idx} for Emergency ID: {e.id} has no assigned resource despite being marked served.")
        processed_emergencies.add(e.id)

    # For emergencies that were not served, add them to UNHANDLED_EMERGENCIES.
    for e in emergencies_with_requirements:
        if e.id not in served_emergency_ids:
            print(f"DEBUG: Emergency ID: {e.id} is unhandled by optimization.")
            UNHANDLED_EMERGENCIES.append(e)

    print(f"DEBUG: Unhandled Emergencies After Dispatch: {len(UNHANDLED_EMERGENCIES)}")
    print(f"=== dispatch_logic complete: {len(assignments)} assignments generated ===")
    return assignments
