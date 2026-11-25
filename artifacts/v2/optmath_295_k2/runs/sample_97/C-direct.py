import gurobipy as gp
from gurobipy import GRB

def solve(params):
    earliest = params["earliest"]
    latest = params["latest"]
    target = params["target"]
    early_cost = params["early_cost"]
    late_cost = params["late_cost"]
    separation = params["separation"]

    n = 5
    aircraft = range(n)
    pairs = [(0,1),(0,2),(0,3),(0,4),(1,2),(1,3),(1,4),(2,3),(2,4),(3,4)]

    # separation may be a list (indexed by pair order) or a dict keyed by tuple
    if isinstance(separation, dict):
        sep_dict = {pair: separation[pair] for pair in pairs}
    else:
        sep_dict = {pair: separation[idx] for idx, pair in enumerate(pairs)}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n, lb=0.0, name="x")
    e = model.addVars(n, lb=0.0, name="e")
    lv = model.addVars(n, lb=0.0, name="lv")
    z = model.addVars(pairs, vtype=GRB.BINARY, name="z")

    for i in aircraft:
        model.addConstr(x[i] >= earliest[i], name=f"earliest_{i}")
        model.addConstr(x[i] <= latest[i], name=f"latest_{i}")

    for i in aircraft:
        model.addConstr(x[i] - target[i] == lv[i] - e[i], name=f"dev_{i}")

    M = max(latest) - min(earliest) + max(sep_dict.values()) + 1

    for (i, j) in pairs:
        sep = sep_dict[(i, j)]
        model.addConstr(
            x[j] - x[i] >= sep - M * (1 - z[i, j]),
            name=f"sep_{i}_{j}_forward"
        )
        model.addConstr(
            x[i] - x[j] >= sep - M * z[i, j],
            name=f"sep_{i}_{j}_reverse"
        )

    model.setObjective(
        gp.quicksum(early_cost[i] * e[i] + late_cost[i] * lv[i] for i in aircraft),
        GRB.MINIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}