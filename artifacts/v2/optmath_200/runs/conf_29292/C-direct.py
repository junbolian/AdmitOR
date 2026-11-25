import gurobipy as gp
from gurobipy import GRB

def solve(params):
    component_cost = params["component_cost"]
    coverage_requirement = params["coverage_requirement"]
    num_components = params["num_components"]
    num_elements = params["num_elements"]

    # Coverage sets: which components can cover each element (1-indexed -> 0-indexed)
    coverage_sets = [
        [0, 5, 7, 12],           # Element 1
        [4, 10, 12, 14],         # Element 2
        [1, 2, 4, 5, 6, 8],      # Element 3
        [1, 2, 6, 7, 10],        # Element 4
        [0, 3, 9, 10, 11],       # Element 5
        [0, 2, 5, 6, 8, 10, 12], # Element 6
        [1, 3, 12],              # Element 7
        [8, 12, 13],             # Element 8
        [2, 3, 5, 8, 12],        # Element 9
        [2, 6, 11, 12],          # Element 10
        [3, 9, 11, 12, 13],      # Element 11
        [3, 7, 11],              # Element 12
        [0, 1, 4, 14],           # Element 13
        [0, 1, 3, 9, 12],        # Element 14
    ]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary decision variables: select component j or not
    x = model.addVars(num_components, vtype=GRB.BINARY, name="x")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(component_cost[j] * x[j] for j in range(num_components)),
        GRB.MINIMIZE
    )

    # Coverage constraints: each element must be covered by at least coverage_requirement[i] components
    for i in range(num_elements):
        req = coverage_requirement[i]
        covering = coverage_sets[i]
        model.addConstr(
            gp.quicksum(x[j] for j in covering) >= req,
            name=f"cover_{i}"
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