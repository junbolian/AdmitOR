import gurobipy as gp
from gurobipy import GRB


def solve(params):
    p = params["processing_time"]

    num_jobs = len(p)
    num_machines = len(p[0]) if num_jobs > 0 else 0

    ops = [(j, m) for j in range(num_jobs) for m in range(num_machines)]

    model = gp.Model("open_shop")
    model.Params.OutputFlag = 0

    S = {}
    for (j, m) in ops:
        S[(j, m)] = model.addVar(lb=0.0, name=f"S_{j}_{m}")

    C = model.addVar(lb=0.0, name="C")

    total_p = sum(p[j][m] for j in range(num_jobs) for m in range(num_machines))
    M_big = total_p + 1.0

    y = {}
    for idx_a, a in enumerate(ops):
        for b in ops[idx_a + 1:]:
            j1, m1 = a
            j2, m2 = b
            same_job = (j1 == j2 and m1 != m2)
            same_mac = (m1 == m2 and j1 != j2)
            if same_job or same_mac:
                y[(a, b)] = model.addVar(vtype=GRB.BINARY, name=f"y_{a}_{b}")
                model.addConstr(S[a] + p[j1][m1] <= S[b] + M_big * (1 - y[(a, b)]))
                model.addConstr(S[b] + p[j2][m2] <= S[a] + M_big * y[(a, b)])

    for a in ops:
        j, m = a
        model.addConstr(C >= S[a] + p[j][m], name=f"completion_{j}_{m}")

    model.setObjective(C, GRB.MINIMIZE)
    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(C.X), "status": "optimal"}

    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "infeasible_or_unbounded"}
    return {"objective": None, "status": "no_optimal"}