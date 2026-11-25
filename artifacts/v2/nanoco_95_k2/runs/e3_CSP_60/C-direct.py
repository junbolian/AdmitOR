import gurobipy as gp
from gurobipy import GRB
from itertools import product as iproduct


def solve(params):
    bolt_length = params["bolt_length"]
    L = [
        params["strip_length_L1"],
        params["strip_length_L2"],
        params["strip_length_L3"],
        params["strip_length_L4"],
    ]
    D = [
        params["demand_D1"],
        params["demand_D2"],
        params["demand_D3"],
        params["demand_D4"],
    ]

    n_types = len(L)

    # Enumerate all feasible cutting patterns (combinations of strip counts per bolt)
    max_counts = [int(bolt_length // L[i]) for i in range(n_types)]

    patterns = []
    ranges = [range(max_counts[i] + 1) for i in range(n_types)]
    for combo in iproduct(*ranges):
        total_length = sum(combo[i] * L[i] for i in range(n_types))
        if total_length <= bolt_length:
            patterns.append(combo)

    n_patterns = len(patterns)

    model = gp.Model("textile_cutting")
    model.setParam("OutputFlag", 0)

    # x[p] = number of bolts cut using pattern p
    x = model.addVars(n_patterns, vtype=GRB.INTEGER, lb=0, name="x")

    # Minimize total bolts used
    model.setObjective(gp.quicksum(x[p] for p in range(n_patterns)), GRB.MINIMIZE)

    # Demand constraints: each strip type must meet its required quantity
    for i in range(n_types):
        model.addConstr(
            gp.quicksum(patterns[p][i] * x[p] for p in range(n_patterns)) >= D[i],
            name=f"demand_{i}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}