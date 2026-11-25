import gurobipy as gp
from gurobipy import GRB


def solve(params):
    jobs = [0, 1, 2]
    ops = [0, 1]
    p = {(j, o): params[f"processing_time_j{j}_o{o}"] for j in jobs for o in ops}
    lag = {j: params[f"precedence_lag_j{j}"] for j in jobs}
    big_m = params["machine_disjunctive_bigM"]

    model = gp.Model("jobshop")
    model.Params.OutputFlag = 0

    keys = [(j, o) for j in jobs for o in ops]
    s = model.addVars(keys, lb=0.0, vtype=GRB.CONTINUOUS, name="s")
    cmax = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="cmax")

    for j in jobs:
        model.addConstr(s[j, 1] >= s[j, 0] + p[j, 0] + lag[j])

    for i in range(len(keys)):
        for k in range(i + 1, len(keys)):
            a = keys[i]
            b = keys[k]
            y = model.addVar(vtype=GRB.BINARY, name=f"y_{a[0]}{a[1]}_{b[0]}{b[1]}")
            model.addConstr(s[a] + p[a] <= s[b] + big_m * (1 - y))
            model.addConstr(s[b] + p[b] <= s[a] + big_m * y)

    for key in keys:
        model.addConstr(cmax >= s[key] + p[key])

    model.setObjective(cmax, GRB.MINIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"status_{model.Status}"}