import gurobipy as gp
from gurobipy import GRB

def solve(params):
    processing_times = params["processing_times"]

    J = range(3)  # batches J0-J2
    M = range(3)  # stations M0-M2

    p = {(j, m): processing_times[j][m] for j in J for m in M}

    # Big-M upper bound: sum of all processing times
    big_M = sum(p[j, m] for j in J for m in M)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Start time of batch j on machine m
    s = model.addVars(J, M, lb=0.0, name="s")

    # Makespan
    C_max = model.addVar(lb=0.0, name="C_max")

    # y[j1, j2, m] = 1 if job j1 precedes job j2 on machine m
    y = model.addVars(J, J, M, vtype=GRB.BINARY, name="y")

    model.setObjective(C_max, GRB.MINIMIZE)

    # Makespan must be at least the completion of every operation
    for j in J:
        for m in M:
            model.addConstr(C_max >= s[j, m] + p[j, m])

    # No overlap on each machine: for each pair of distinct jobs on each machine
    for m in M:
        for j1 in J:
            for j2 in J:
                if j1 < j2:
                    # Either j1 before j2, or j2 before j1
                    model.addConstr(
                        s[j1, m] + p[j1, m] <= s[j2, m] + big_M * (1 - y[j1, j2, m])
                    )
                    model.addConstr(
                        s[j2, m] + p[j2, m] <= s[j1, m] + big_M * y[j1, j2, m]
                    )

    # No overlap for each batch: each batch can be on at most one machine at a time
    # For each job j and each pair of distinct machines, one operation must precede the other
    z = model.addVars(J, M, M, vtype=GRB.BINARY, name="z")

    for j in J:
        for m1 in M:
            for m2 in M:
                if m1 < m2:
                    model.addConstr(
                        s[j, m1] + p[j, m1] <= s[j, m2] + big_M * (1 - z[j, m1, m2])
                    )
                    model.addConstr(
                        s[j, m2] + p[j, m2] <= s[j, m1] + big_M * z[j, m1, m2]
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