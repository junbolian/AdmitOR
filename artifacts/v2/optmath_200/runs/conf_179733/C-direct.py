import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cargo_weights = params["cargo_weights"]
    vehicle_capacity = params["vehicle_capacity"]

    n_items = len(cargo_weights)
    # Upper bound on vehicles needed: each item in its own vehicle
    n_vehicles = n_items

    items = range(n_items)
    vehicles = range(n_vehicles)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # y[v] = 1 if vehicle v is used
    y = model.addVars(vehicles, vtype=GRB.BINARY, name="y")
    # x[i,v] = 1 if cargo item i is assigned to vehicle v
    x = model.addVars(items, vehicles, vtype=GRB.BINARY, name="x")

    # Objective: minimize number of vehicles used
    model.setObjective(gp.quicksum(y[v] for v in vehicles), GRB.MINIMIZE)

    # Each cargo item assigned to exactly one vehicle
    for i in items:
        model.addConstr(gp.quicksum(x[i, v] for v in vehicles) == 1, name=f"assign_{i}")

    # Capacity constraints
    for v in vehicles:
        model.addConstr(
            gp.quicksum(cargo_weights[i] * x[i, v] for i in items) <= vehicle_capacity * y[v],
            name=f"capacity_{v}"
        )

    # If items are assigned to a vehicle, the vehicle must be used
    for i in items:
        for v in vehicles:
            model.addConstr(x[i, v] <= y[v], name=f"link_{i}_{v}")

    # Symmetry breaking: vehicle v can only be used if v-1 is used
    for v in range(1, n_vehicles):
        model.addConstr(y[v] <= y[v - 1], name=f"sym_{v}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}