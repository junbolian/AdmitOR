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

    # separation_raw is a list of 12 values corresponding to these ordered pairs:
    # (0<1, 1<0, 0<2, 2<0, 0<3, 3<0, 1<2, 2<1, 1<3, 3<1, 2<3, 3<2)
    pair_order = [(0,1),(1,0),(0,2),(2,0),(0,3),(3,0),(1,2),(2,1),(1,3),(3,1),(2,3),(3,2)]
    separation = {pair_order[k]: separation_raw[k] for k in range(len(pair_order))}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n, lb=[earliest[i] for i in aircraft],
                         ub=[latest[i] for i in aircraft],
                         vtype=GRB.CONTINUOUS, name="x")

    e = model.addVars(n, lb=0.0, vtype=GRB.CONTINUOUS, name="e")
    late = model.addVars(n, lb=0.0, vtype=GRB.CONTINUOUS, name="late")

    z = model.addVars(n, n, vtype=GRB.BINARY, name="z")

    for i in aircraft:
        model.addConstr(e[i] >= target[i] - x[i], name=f"early_{i}")
        model.addConstr(late[i] >= x[i] - target[i], name=f"late_{i}")

    for (i, j) in pair_order:
        if i < j:
            model.addConstr(z[i,j] + z[j,i] == 1, name=f"order_{i}_{j}")

    M = max(latest) - min(earliest) + max(separation.values())

    for (i, j) in pair_order:
        s_ij = separation[(i, j)]
        model.addConstr(
            x[j] - x[i] >= s_ij - M * (1 - z[i,j]),
            name=f"sep_{i}_{j}"
        )

    obj = gp.quicksum(
        early_penalty[i] * e[i] + late_penalty[i] * late[i]
        for i in aircraft
    )
    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}