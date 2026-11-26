import gurobipy as gp
from gurobipy import GRB


def solve(params):
    demand_3m = params["demand_3m"]
    demand_4m = params["demand_4m"]
    raw_length = params["raw_length"]
    len_3 = params["piece_length_3m"]
    len_4 = params["piece_length_4m"]

    # Enumerate all feasible cutting patterns (a pieces of 3m, b pieces of 4m)
    patterns = []
    for a in range(int(raw_length // len_3) + 1):
        for b in range(int((raw_length - a * len_3) // len_4) + 1):
            patterns.append((a, b))

    model = gp.Model("steel_cutting")
    model.Params.OutputFlag = 0

    x = model.addVars(len(patterns), vtype=GRB.CONTINUOUS, lb=0.0, name="x")

    model.setObjective(gp.quicksum(x[p] for p in range(len(patterns))), GRB.MINIMIZE)

    model.addConstr(
        gp.quicksum(patterns[p][0] * x[p] for p in range(len(patterns))) >= demand_3m,
        name="demand_3m",
    )
    model.addConstr(
        gp.quicksum(patterns[p][1] * x[p] for p in range(len(patterns))) >= demand_4m,
        name="demand_4m",
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}