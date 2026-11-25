import gurobipy as gp
from gurobipy import GRB

def solve(params):
    p = {}
    jobs = [0, 1, 2]
    machines = [0, 1, 2]

    for j in jobs:
        for m in machines:
            p[(j, m)] = params[f"p_J{j}_M{m}"]

    # Big-M for disjunctive constraints
    BIG_M = sum(p[(j, m)] for j in jobs for m in machines)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Start time of job j on machine m
    start = {}
    for j in jobs:
        for m in machines:
            start[(j, m)] = model.addVar(lb=0.0, name=f"start_J{j}_M{m}")

    # Makespan
    Cmax = model.addVar(lb=0.0, name="Cmax")

    # Binary: job j is processed before job k on machine m
    y = {}
    for m in machines:
        for j in jobs:
            for k in jobs:
                if j < k:
                    y[(j, k, m)] = model.addVar(vtype=GRB.BINARY, name=f"y_{j}_{k}_m{m}")

    model.setObjective(Cmax, GRB.MINIMIZE)

    # Makespan >= completion of every operation
    for j in jobs:
        for m in machines:
            model.addConstr(Cmax >= start[(j, m)] + p[(j, m)], name=f"cmax_J{j}_M{m}")

    # Machine disjunctive constraints: no two jobs overlap on the same machine
    for m in machines:
        for j in jobs:
            for k in jobs:
                if j < k:
                    yv = y[(j, k, m)]
                    # Either j before k, or k before j
                    model.addConstr(
                        start[(j, m)] + p[(j, m)] <= start[(k, m)] + BIG_M * (1 - yv),
                        name=f"mach_jk_m{m}_J{j}J{k}"
                    )
                    model.addConstr(
                        start[(k, m)] + p[(k, m)] <= start[(j, m)] + BIG_M * yv,
                        name=f"mach_kj_m{m}_J{j}J{k}"
                    )

    # Job disjunctive constraints: each job can only be on one machine at a time
    # Binary: job j is processed on machine ma before machine mb
    z = {}
    for j in jobs:
        for ma in machines:
            for mb in machines:
                if ma < mb:
                    z[(j, ma, mb)] = model.addVar(vtype=GRB.BINARY, name=f"z_J{j}_m{ma}m{mb}")

    for j in jobs:
        for ma in machines:
            for mb in machines:
                if ma < mb:
                    zv = z[(j, ma, mb)]
                    model.addConstr(
                        start[(j, ma)] + p[(j, ma)] <= start[(j, mb)] + BIG_M * (1 - zv),
                        name=f"job_ab_J{j}_m{ma}m{mb}"
                    )
                    model.addConstr(
                        start[(j, mb)] + p[(j, mb)] <= start[(j, ma)] + BIG_M * zv,
                        name=f"job_ba_J{j}_m{ma}m{mb}"
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