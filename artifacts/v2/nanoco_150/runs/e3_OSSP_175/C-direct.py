import gurobipy as gp
from gurobipy import GRB

def solve(params):
    processing_times = params["processing_times"]

    jobs = list(range(len(processing_times)))
    machines = list(range(len(processing_times[0])))

    # Big-M upper bound
    M_big = sum(processing_times[j][m] for j in jobs for m in machines) + 1

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Start time for job j on machine m
    start = {
        (j, m): model.addVar(lb=0.0, name=f"start_{j}_{m}")
        for j in jobs for m in machines
    }

    # Makespan
    makespan = model.addVar(lb=0.0, name="makespan")

    # Binary: y[j1, j2, m] = 1 if job j1 precedes job j2 on machine m
    y = {
        (j1, j2, m): model.addVar(vtype=GRB.BINARY, name=f"y_{j1}_{j2}_{m}")
        for j1 in jobs for j2 in jobs if j1 != j2
        for m in machines
    }

    model.setObjective(makespan, GRB.MINIMIZE)

    # Makespan must be >= completion time of every job on every machine
    for j in jobs:
        for m in machines:
            p = processing_times[j][m]
            model.addConstr(makespan >= start[j, m] + p, name=f"mkspan_{j}_{m}")

    # No overlap on each machine: for each pair (j1, j2) on machine m,
    # exactly one of y[j1,j2,m] or y[j2,j1,m] is 1
    for j1 in jobs:
        for j2 in jobs:
            if j1 >= j2:
                continue
            for m in machines:
                p1 = processing_times[j1][m]
                p2 = processing_times[j2][m]
                # Mutual exclusion
                model.addConstr(
                    y[j1, j2, m] + y[j2, j1, m] == 1,
                    name=f"mutex_{j1}_{j2}_{m}"
                )
                # If j1 before j2: start[j1,m] + p1 <= start[j2,m]
                model.addConstr(
                    start[j1, m] + p1 <= start[j2, m] + M_big * (1 - y[j1, j2, m]),
                    name=f"seq_{j1}_{j2}_{m}_a"
                )
                # If j2 before j1: start[j2,m] + p2 <= start[j1,m]
                model.addConstr(
                    start[j2, m] + p2 <= start[j1, m] + M_big * (1 - y[j2, j1, m]),
                    name=f"seq_{j2}_{j1}_{m}_b"
                )

    # No overlap on each job: for each pair (m1, m2) on job j,
    # exactly one of z[j,m1,m2] or z[j,m2,m1] is 1
    z = {
        (j, m1, m2): model.addVar(vtype=GRB.BINARY, name=f"z_{j}_{m1}_{m2}")
        for j in jobs for m1 in machines for m2 in machines if m1 != m2
    }

    for j in jobs:
        for m1 in machines:
            for m2 in machines:
                if m1 >= m2:
                    continue
                p1 = processing_times[j][m1]
                p2 = processing_times[j][m2]
                model.addConstr(
                    z[j, m1, m2] + z[j, m2, m1] == 1,
                    name=f"job_mutex_{j}_{m1}_{m2}"
                )
                model.addConstr(
                    start[j, m1] + p1 <= start[j, m2] + M_big * (1 - z[j, m1, m2]),
                    name=f"job_seq_{j}_{m1}_{m2}_a"
                )
                model.addConstr(
                    start[j, m2] + p2 <= start[j, m1] + M_big * (1 - z[j, m2, m1]),
                    name=f"job_seq_{j}_{m2}_{m1}_b"
                )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}