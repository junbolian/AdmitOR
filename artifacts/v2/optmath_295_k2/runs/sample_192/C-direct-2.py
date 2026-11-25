import gurobipy as gp
from gurobipy import GRB

def solve(params):
    earliest = params["earliest"]
    latest = params["latest"]
    target = params["target"]
    early_penalty = params["early_penalty"]
    late_penalty = params["late_penalty"]
    separation_raw = params["separation"]

    n = 4
    aircraft = range(n)

    # separation is a list of values corresponding to ordered pairs:
    # (0<1, 1<0, 0<2, 2<0, 0<3, 3<0, 1<2, 2<1, 1<3, 3<1, 2<3, 3<2)
    pair_order = [
        (0, 1), (1, 0), (0, 2), (2, 0), (0, 3), (3, 0),
        (1, 2), (2, 1), (1, 3), (3, 1), (2, 3), (3, 2)
    ]
    sep = {}
    for idx, (i, j) in enumerate(pair_order):
        sep[(i, j)] = separation_raw[idx]

    M = 10000

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n, lb=0.0, name="x")
    e = model.addVars(n, lb=0.0, name="e")
    late = model.addVars(n, lb=0.0, name="late")

    pairs = [(i, j) for i in aircraft for j in aircraft if i < j]
    z = model.addVars(pairs, vtype=GRB.BINARY, name="z")

    for i in aircraft:
        model.addConstr(x[i] >= earliest[i], name=f"earliest_{i}")
        model.addConstr(x[i] <= latest[i], name=f"latest_{i}")

    for i in aircraft:
        model.addConstr(e[i] >= target[i] - x[i], name=f"early_dev_{i}")
        model.addConstr(late[i] >= x[i] - target[i], name=f"late_dev_{i}")

    for (i, j) in pairs:
        if (i, j) in sep:
            model.addConstr(
                x[j] - x[i] >= sep[(i, j)] - M * (1 - z[i, j]),
                name=f"sep_{i}_before_{j}"
            )
        if (j, i) in sep:
            model.addConstr(
                x[i] - x[j] >= sep[(j, i)] - M * z[i, j],
                name=f"sep_{j}_before_{i}"
            )

    model.setObjective(
        gp.quicksum(early_penalty[i] * e[i] + late_penalty[i] * late[i] for i in aircraft),
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