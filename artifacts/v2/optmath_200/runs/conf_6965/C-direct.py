import gurobipy as gp
from gurobipy import GRB

def solve(params):
    select_limit = params["select_limit"]
    dispersion_raw = params["dispersion"]

    # Handle both dict and list formats
    if isinstance(dispersion_raw, dict):
        dispersion = dispersion_raw
    else:
        # Assume list of [i, j, value] or [[i, j], value] or similar
        # Try to convert list-of-pairs to dict
        dispersion = {}
        for item in dispersion_raw:
            if len(item) == 3:
                dispersion[(item[0], item[1])] = item[2]
            elif len(item) == 2:
                key, val = item
                dispersion[(key[0], key[1])] = val

    # Infer node set from dispersion keys
    nodes = sorted(set(i for (i, j) in dispersion.keys()) | set(j for (i, j) in dispersion.keys()))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: select facility i
    x = model.addVars(nodes, vtype=GRB.BINARY, name="x")

    # Binary variable: pair (i,j) both selected
    y = model.addVars(list(dispersion.keys()), vtype=GRB.BINARY, name="y")

    # Objective: maximize total dispersion
    model.setObjective(
        gp.quicksum(dispersion[(i, j)] * y[i, j] for (i, j) in dispersion.keys()),
        GRB.MAXIMIZE
    )

    # Exactly select_limit facilities selected
    model.addConstr(gp.quicksum(x[i] for i in nodes) == select_limit, name="select_limit")

    # Pairwise activation constraints
    for (i, j) in dispersion.keys():
        model.addConstr(y[i, j] <= x[i], name=f"act_i_{i}_{j}")
        model.addConstr(y[i, j] <= x[j], name=f"act_j_{i}_{j}")
        model.addConstr(y[i, j] >= x[i] + x[j] - 1, name=f"act_lb_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}