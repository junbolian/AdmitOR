import gurobipy as gp
from gurobipy import GRB

def solve(params):
    processing_times = params["processing_times"]
    num_jobs = params["num_jobs"]
    num_stations = params["num_stations"]

    jobs = range(num_jobs)
    stations = range(num_stations)

    # Big-M for disjunctive constraints
    M = sum(processing_times[j][s] for j in jobs for s in stations) * 2

    model = gp.Model("flowshop_makespan")
    model.setParam("OutputFlag", 0)

    # Start times: S[j][s] = start time of job j on station s
    S = [[model.addVar(lb=0.0, name=f"S_{j}_{s}") for s in stations] for j in jobs]

    # Makespan variable
    C_max = model.addVar(lb=0.0, name="C_max")

    # Binary: y[j][k] = 1 if job j precedes job k on a station
    y = {(j, k): model.addVar(vtype=GRB.BINARY, name=f"y_{j}_{k}")
         for j in jobs for k in jobs if j != k}

    model.update()

    # 1. Technological order: each job must complete on station s before starting station s+1
    for j in jobs:
        for s in range(num_stations - 1):
            model.addConstr(S[j][s + 1] >= S[j][s] + processing_times[j][s],
                            name=f"tech_{j}_{s}")

    # 2. Machine capacity: no two jobs overlap on the same station (disjunctive)
    for s in stations:
        for j in jobs:
            for k in jobs:
                if j < k:
                    # Either j before k, or k before j
                    model.addConstr(
                        S[k][s] >= S[j][s] + processing_times[j][s] - M * (1 - y[j, k]),
                        name=f"disj1_{j}_{k}_{s}"
                    )
                    model.addConstr(
                        S[j][s] >= S[k][s] + processing_times[k][s] - M * y[j, k],
                        name=f"disj2_{j}_{k}_{s}"
                    )

    # 3. Makespan >= completion of every job on last station
    last = num_stations - 1
    for j in jobs:
        model.addConstr(C_max >= S[j][last] + processing_times[j][last],
                        name=f"makespan_{j}")

    # Objective: minimize makespan
    model.setObjective(C_max, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}