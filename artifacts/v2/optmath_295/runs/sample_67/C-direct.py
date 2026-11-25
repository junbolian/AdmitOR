import gurobipy as gp
from gurobipy import GRB

def solve(params):
    hub_costs = params["hub_costs"]

    # Route coverage: route index (0-based) -> list of hub indices (0-based)
    coverage = [
        [1, 2, 3, 6, 10, 12],        # Route 1
        [9, 11, 14],                   # Route 2
        [0, 4, 5, 7, 10, 11, 12, 13], # Route 3
        [1, 2, 3, 5, 6, 9, 11, 13],   # Route 4
        [0, 1, 2, 9, 12],             # Route 5
        [0, 1, 2, 5, 7, 9, 10, 11, 13], # Route 6
        [2, 3, 4, 6, 7, 9, 10, 12, 13], # Route 7
        [0, 1, 2, 6, 8, 11, 12],      # Route 8
        [0, 3, 6, 9, 11, 12, 13],     # Route 9
        [0, 2, 3, 4, 6, 9, 10, 12, 13, 14], # Route 10
        [0, 3, 6, 8, 12, 13],         # Route 11
        [2, 3, 5, 7, 9, 10, 11, 12, 13, 14], # Route 12
        [0, 1, 3, 4, 6, 10, 12, 13],  # Route 13
        [0, 3, 4, 5, 8, 11, 13, 14],  # Route 14
        [1, 5, 6, 11, 12, 13],        # Route 15
        [0, 3, 7, 10, 11, 13, 14],    # Route 16
    ]

    num_hubs = 15
    num_routes = 16

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary decision variables: activate hub h or not
    x = model.addVars(num_hubs, vtype=GRB.BINARY, name="x")

    # Objective: minimize total activation cost
    model.setObjective(
        gp.quicksum(hub_costs[h] * x[h] for h in range(num_hubs)),
        GRB.MINIMIZE
    )

    # Coverage constraints: each route must be covered by at least one active hub
    for r in range(num_routes):
        model.addConstr(
            gp.quicksum(x[h] for h in coverage[r]) >= 1,
            name=f"cover_route_{r}"
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