import gurobipy as gp
from gurobipy import GRB


def solve(params):
    L = params["standard_rebar_length"]
    d18 = params["demand_18"]
    d20 = params["demand_20"]
    d56 = params["demand_56"]
    l18 = params["piece_length_18"]
    l20 = params["piece_length_20"]
    l56 = params["piece_length_56"]

    tol = 1e-9

    # Enumerate all feasible cutting patterns (a, b, c):
    # a pieces of length l18, b of l20, c of l56 cut from one standard rebar.
    patterns = []
    max_a = int(L // l18) if l18 > tol else 0
    max_b = int(L // l20) if l20 > tol else 0
    max_c = int(L // l56) if l56 > tol else 0
    for a in range(max_a + 1):
        for b in range(max_b + 1):
            for c in range(max_c + 1):
                if a * l18 + b * l20 + c * l56 <= L + tol:
                    patterns.append((a, b, c))

    if not patterns:
        return {"objective": None, "status": "no_patterns"}

    model = gp.Model("rebar_cutting")
    model.Params.OutputFlag = 0

    x = model.addVars(len(patterns), vtype=GRB.INTEGER, lb=0, name="x")
    model.setObjective(gp.quicksum(x[p] for p in range(len(patterns))), GRB.MINIMIZE)

    model.addConstr(
        gp.quicksum(patterns[p][0] * x[p] for p in range(len(patterns))) == d18,
        "demand_18",
    )
    model.addConstr(
        gp.quicksum(patterns[p][1] * x[p] for p in range(len(patterns))) == d20,
        "demand_20",
    )
    model.addConstr(
        gp.quicksum(patterns[p][2] * x[p] for p in range(len(patterns))) == d56,
        "demand_56",
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "not_optimal"}