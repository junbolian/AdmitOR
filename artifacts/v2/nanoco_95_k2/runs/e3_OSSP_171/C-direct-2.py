import gurobipy as gp
from gurobipy import GRB

def solve(params):
    p = {}
    jobs = [0, 1, 2]
    machines = [0, 1, 2]

    for j in jobs:
        for m in machines:
            p[(j, m)] = params[f"p_J{j}_M{m}"]

    BIG_M = sum(p[(j, m)] for j in jobs for m in machines)

    model = gp.Model("open_shop")
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 120)

    # Start time of job j on machine m
    s = {}
    for j in jobs:
        for m in machines:
            s[(j, m)] = model.addVar(lb=0.0, name=f"s_J{j}_M{m}")

    # Makespan
    C_max = model.addVar(lb=0.0, name="C_max")

    # Binary: delta_jk_m = 1 if job j precedes job k on machine m
    delta = {}
    for m in machines:
        for j in jobs:
            for k in jobs:
                if j != k:
                    delta[(j, k, m)] = model.addVar(vtype=GRB.BINARY, name=f"delta_J{j}_J{k}_M{m}")

    # Binary: gamma_j_mn = 1 if job j visits machine m before machine n
    gamma = {}
    for j in jobs:
        for m in machines:
            for n in machines:
                if m != n:
                    gamma[(j, m, n)] = model.addVar(vtype=GRB.BINARY, name=f"gamma_J{j}_M{m}_M{n}")

    model.update()

    # Makespan >= completion of every operation
    for j in jobs:
        for m in machines:
            model.addConstr(C_max >= s[(j, m)] + p[(j, m)], name=f"mksp_J{j}_M{m}")

    # Machine disjunctive constraints: no two jobs overlap on the same machine
    for m in machines:
        for j in jobs:
            for k in jobs:
                if j < k:
                    # Either j before k, or k before j
                    model.addConstr(
                        delta[(j, k, m)] + delta[(k, j, m)] == 1,
                        name=f"mach_one_dir_J{j}_J{k}_M{m}"
                    )
                    model.addConstr(
                        s[(j, m)] + p[(j, m)] <= s[(k, m)] + BIG_M * (1 - delta[(j, k, m)]),
                        name=f"mach_jk_J{j}_J{k}_M{m}"
                    )
                    model.addConstr(
                        s[(k, m)] + p[(k, m)] <= s[(j, m)] + BIG_M * (1 - delta[(k, j, m)]),
                        name=f"mach_kj_J{j}_J{k}_M{m}"
                    )

    # Job disjunctive constraints: each job on at most one machine at a time
    for j in jobs:
        for m in machines:
            for n in machines:
                if m < n:
                    model.addConstr(
                        gamma[(j, m, n)] + gamma[(j, n, m)] == 1,
                        name=f"job_one_dir_J{j}_M{m}_M{n}"
                    )
                    model.addConstr(
                        s[(j, m)] + p[(j, m)] <= s[(j, n)] + BIG_M * (1 - gamma[(j, m, n)]),
                        name=f"job_mn_J{j}_M{m}_M{n}"
                    )
                    model.addConstr(
                        s[(j, n)] + p[(j, n)] <= s[(j, m)] + BIG_M * (1 - gamma[(j, n, m)]),
                        name=f"job_nm_J{j}_M{m}_M{n}"
                    )

    model.setObjective(C_max, GRB.MINIMIZE)
    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        if model.SolCount > 0:
            return {"objective": model.ObjVal, "status": "optimal"}
        return {"objective": None, "status": "time_limit_no_solution"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}