import gurobipy as gp
from gurobipy import GRB


def solve(params):
    jobs = [0, 1, 2]
    machines = [0, 1, 2]
    p = {}
    for i in jobs:
        for j in machines:
            p[(i, j)] = float(params[f"processing_time_J{i}_M{j}"])

    BigM = sum(p.values()) + 1.0

    model = gp.Model("open_shop")
    model.Params.OutputFlag = 0

    s = {}
    for i in jobs:
        for j in machines:
            s[(i, j)] = model.addVar(lb=0.0, name=f"s_{i}_{j}")

    Cmax = model.addVar(lb=0.0, name="Cmax")

    x = {}
    for i in jobs:
        for k in jobs:
            if i < k:
                for j in machines:
                    x[(i, k, j)] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{k}_{j}")

    y = {}
    for i in jobs:
        for j in machines:
            for l in machines:
                if j < l:
                    y[(i, j, l)] = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{j}_{l}")

    for i in jobs:
        for j in machines:
            model.addConstr(Cmax >= s[(i, j)] + p[(i, j)], name=f"makespan_{i}_{j}")

    for i in jobs:
        for k in jobs:
            if i < k:
                for j in machines:
                    model.addConstr(
                        s[(i, j)] + p[(i, j)] <= s[(k, j)] + BigM * (1 - x[(i, k, j)]),
                        name=f"mach_ord_a_{i}_{k}_{j}",
                    )
                    model.addConstr(
                        s[(k, j)] + p[(k, j)] <= s[(i, j)] + BigM * x[(i, k, j)],
                        name=f"mach_ord_b_{i}_{k}_{j}",
                    )

    for i in jobs:
        for j in machines:
            for l in machines:
                if j < l:
                    model.addConstr(
                        s[(i, j)] + p[(i, j)] <= s[(i, l)] + BigM * (1 - y[(i, j, l)]),
                        name=f"job_ord_a_{i}_{j}_{l}",
                    )
                    model.addConstr(
                        s[(i, l)] + p[(i, l)] <= s[(i, j)] + BigM * y[(i, j, l)],
                        name=f"job_ord_b_{i}_{j}_{l}",
                    )

    model.setObjective(Cmax, GRB.MINIMIZE)
    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}