import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = [
        params["cost_vehicle_1"],
        params["cost_vehicle_2"],
        params["cost_vehicle_3"],
        params["cost_vehicle_4"],
        params["cost_vehicle_5"],
        params["cost_vehicle_6"],
    ]

    # Coverage constraints: each route requires at least one of the listed vehicles (0-indexed)
    coverage = [
        [5],           # Route 1
        [1, 3, 5],     # Route 2
        [0, 2, 3],     # Route 3
        [2],           # Route 4
        [0, 4, 5],     # Route 5
        [0, 3],        # Route 6
        [2, 4],        # Route 7
        [3],           # Route 8
        [2, 4, 5],     # Route 9
        [3, 4, 5],     # Route 10
        [2, 3],        # Route 11
        [0, 2, 4, 5],  # Route 12
        [2, 3, 5],     # Route 13
    ]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(6, vtype=GRB.BINARY, name="x")

    model.setObjective(gp.quicksum(cost[v] * x[v] for v in range(6)), GRB.MINIMIZE)

    for route_idx, vehicles in enumerate(coverage):
        model.addConstr(
            gp.quicksum(x[v] for v in vehicles) >= 1,
            name=f"route_{route_idx + 1}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}