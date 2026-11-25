import gurobipy as gp
from gurobipy import GRB

def solve(params):
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    preference = params["preference"]
    assignment_value = params["assignment_value"]

    num_participants = len(preference)
    num_cars = len(preference[0]) if num_participants > 0 else 0

    model = gp.Model("car_assignment")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[p][c] = 1 if participant p assigned to car c
    x = {}
    for p in range(num_participants):
        for c in range(num_cars):
            if preference[p][c] == 1:
                x[p, c] = model.addVar(vtype=GRB.BINARY, name=f"x_{p}_{c}")

    # Objective: maximize total assignment value
    # assignment_value may be a scalar or a 2D matrix
    if isinstance(assignment_value, (int, float)):
        obj_expr = gp.quicksum(float(assignment_value) * x[p, c] for (p, c) in x)
    else:
        # treat as 2D indexable
        obj_expr = gp.quicksum(float(assignment_value[p][c]) * x[p, c] for (p, c) in x)

    model.setObjective(obj_expr, GRB.MAXIMIZE)

    # Helper to get per-index capacity as a float
    def get_cap(cap, idx):
        if isinstance(cap, (int, float)):
            return float(cap)
        else:
            return float(cap[idx])

    # Each participant assigned to at most participant_capacity cars
    for p in range(num_participants):
        assigned_vars = [x[p, c] for c in range(num_cars) if (p, c) in x]
        if assigned_vars:
            model.addConstr(
                gp.quicksum(assigned_vars) <= get_cap(participant_capacity, p),
                name=f"part_cap_{p}"
            )

    # Each car assigned to at most car_capacity participants
    for c in range(num_cars):
        assigned_vars = [x[p, c] for p in range(num_participants) if (p, c) in x]
        if assigned_vars:
            model.addConstr(
                gp.quicksum(assigned_vars) <= get_cap(car_capacity, c),
                name=f"car_cap_{c}"
            )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{status}"}