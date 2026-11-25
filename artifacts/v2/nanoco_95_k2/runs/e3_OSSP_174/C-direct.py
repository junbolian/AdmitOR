import gurobipy as gp
from gurobipy import GRB

def solve(params):
    processing_time = params["processing_time"]

    jobs = ["J0", "J1", "J2"]
    machines = ["M0", "M1", "M2"]

    # processing_time is a list of lists indexed by integer positions
    # J0->0, J1->1, J2->2 and M0->0, M1->1, M2->2
    job_idx = {j: i for i, j in enumerate(jobs)}
    mach_idx = {m: i for i, m in enumerate(machines)}

    def pt(j, m):
        return processing_time[job_idx[j]][mach_idx[m]]

    M_big = sum(pt(j, m) for j in jobs for m in machines)

    model = gp.Model("flexible_job_shop")
    model.setParam("OutputFlag", 0)

    start = {
        (j, m): model.addVar(lb=0.0, name=f"start_{j}_{m}")
        for j in jobs for m in machines
    }

    makespan = model.addVar(lb=0.0, name="makespan")

    x = {
        (j1, j2, m): model.addVar(vtype=GRB.BINARY, name=f"x_{j1}_{j2}_{m}")
        for j1 in jobs for j2 in jobs if j1 != j2
        for m in machines
    }

    y = {
        (j, m1, m2): model.addVar(vtype=GRB.BINARY, name=f"y_{j}_{m1}_{m2}")
        for j in jobs
        for m1 in machines for m2 in machines if m1 != m2
    }

    model.setObjective(makespan, GRB.MINIMIZE)

    for j in jobs:
        for m in machines:
            model.addConstr(
                makespan >= start[j, m] + pt(j, m),
                name=f"makespan_{j}_{m}"
            )

    for m in machines:
        for j1 in jobs:
            for j2 in jobs:
                if j1 >= j2:
                    continue
                model.addConstr(
                    start[j1, m] + pt(j1, m) <=
                    start[j2, m] + M_big * (1 - x[j1, j2, m]),
                    name=f"no_overlap_{j1}_{j2}_{m}_a"
                )
                model.addConstr(
                    start[j2, m] + pt(j2, m) <=
                    start[j1, m] + M_big * x[j1, j2, m],
                    name=f"no_overlap_{j1}_{j2}_{m}_b"
                )

    for j in jobs:
        for m1 in machines:
            for m2 in machines:
                if m1 >= m2:
                    continue
                model.addConstr(
                    start[j, m1] + pt(j, m1) <=
                    start[j, m2] + M_big * (1 - y[j, m1, m2]),
                    name=f"job_seq_{j}_{m1}_{m2}_a"
                )
                model.addConstr(
                    start[j, m2] + pt(j, m2) <=
                    start[j, m1] + M_big * y[j, m1, m2],
                    name=f"job_seq_{j}_{m1}_{m2}_b"
                )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        if model.SolCount > 0:
            return {"objective": model.ObjVal, "status": "optimal"}
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}