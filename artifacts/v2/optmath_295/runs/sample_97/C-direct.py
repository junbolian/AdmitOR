import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 5
    pairs = [(i, j) for i in range(n) for j in range(i+1, n)]

    earliest = [params[f"earliest_{i}"] for i in range(n)]
    latest   = [params[f"latest_{i}"]   for i in range(n)]
    target   = [params[f"target_{i}"]   for i in range(n)]
    early_cost = [params[f"early_cost_{i}"] for i in range(n)]
    late_cost  = [params[f"late_cost_{i}"]  for i in range(n)]
    sep = {(i, j): params[f"sep_{i}_{j}"] for i, j in pairs}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Landing time variables
    x = [model.addVar(lb=earliest[i], ub=latest[i], name=f"x_{i}") for i in range(n)]

    # Early/late deviation variables
    e = [model.addVar(lb=0.0, name=f"e_{i}") for i in range(n)]
    l = [model.addVar(lb=0.0, name=f"l_{i}") for i in range(n)]

    # Binary ordering variables: z[i,j] = 1 if aircraft i lands before aircraft j
    z = {(i, j): model.addVar(vtype=GRB.BINARY, name=f"z_{i}_{j}") for i, j in pairs}

    model.update()

    # Deviation constraints: x[i] - target[i] = l[i] - e[i]
    for i in range(n):
        model.addConstr(x[i] - target[i] == l[i] - e[i], name=f"dev_{i}")

    # Separation constraints with big-M
    # If z[i,j] = 1: x[j] >= x[i] + sep[i,j]
    # If z[i,j] = 0: x[i] >= x[j] + sep[i,j]
    # Big-M: max possible difference in landing times
    M = max(latest) - min(earliest)

    for i, j in pairs:
        s = sep[(i, j)]
        model.addConstr(
            x[j] >= x[i] + s - M * (1 - z[(i, j)]),
            name=f"sep_ij_{i}_{j}"
        )
        model.addConstr(
            x[i] >= x[j] + s - M * z[(i, j)],
            name=f"sep_ji_{i}_{j}"
        )

    # Objective: minimize total penalty
    obj = gp.quicksum(early_cost[i] * e[i] + late_cost[i] * l[i] for i in range(n))
    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}