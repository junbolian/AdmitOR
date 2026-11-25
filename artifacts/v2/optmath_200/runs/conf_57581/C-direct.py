import gurobipy as gp
from gurobipy import GRB

def solve(params):
    selection_cost = params["selection_cost"]
    coverage_requirement = params["coverage_requirement"]

    # Coverage constraint sets (0-indexed locations)
    coverage_sets = [
        [1, 5, 7, 9, 10, 11],   # constraint 1
        [6, 8, 10, 11],          # constraint 2
        [1, 4, 6, 8, 9, 11],    # constraint 3
        [0, 1, 2, 4, 5, 9, 10, 11],  # constraint 4
        [3, 6, 9, 10, 11],       # constraint 5
        [0, 1, 2, 3],            # constraint 6
        [0, 1, 2, 5, 6, 7],     # constraint 7
        [0, 2, 4, 6, 11],        # constraint 8
        [3, 4, 7, 8, 9],         # constraint 9
        [4, 5, 9],               # constraint 10
        [1, 4, 8, 11],           # constraint 11
        [1, 2, 3, 4, 7],         # constraint 12
        [1, 2, 5, 6],            # constraint 13
        [6, 7],                  # constraint 14
        [1, 5, 6, 8],            # constraint 15
        [0, 2, 5, 7, 11],        # constraint 16
        [2, 3, 4, 5, 11],        # constraint 17
        [3, 6, 7, 10],           # constraint 18
        [2, 3, 5, 6, 9],         # constraint 19
        [0, 2, 5, 7],            # constraint 20
        [0, 2, 3, 6, 8, 9],      # constraint 21
    ]

    n_locations = 12
    n_constraints = 21

    model = gp.Model("location_selection")
    model.setParam("OutputFlag", 0)

    # Binary decision variables
    x = model.addVars(n_locations, vtype=GRB.BINARY, name="x")

    # Objective: minimize total selection cost
    model.setObjective(
        gp.quicksum(selection_cost[i] * x[i] for i in range(n_locations)),
        GRB.MINIMIZE
    )

    # Coverage constraints
    for c in range(n_constraints):
        locs = coverage_sets[c]
        req = coverage_requirement[c]
        model.addConstr(
            gp.quicksum(x[i] for i in locs) >= req,
            name=f"coverage_{c}"
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