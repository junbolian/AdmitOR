import gurobipy as gp
from gurobipy import GRB

def solve(params):
    processing_times = params["processing_times"]

    n_jobs = 3
    n_stations = 3
    jobs = range(n_jobs)
    stations = range(n_stations)

    # Big-M for disjunctive constraints
    M = sum(processing_times[j][s] for j in jobs for s in stations) + 1

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Start times: start[j][s] = start time of job j on station s
    start = [[model.addVar(lb=0, name=f"start_{j}_{s}") for s in stations] for j in jobs]

    # Makespan variable
    makespan = model.addVar(lb=0, name="makespan")

    # Objective: minimize makespan
    model.setObjective(makespan, GRB.MINIMIZE)

    # 1. Technological order: each job must complete station s before starting station s+1
    for j in jobs:
        for s in range(n_stations - 1):
            model.addConstr(
                start[j][s + 1] >= start[j][s] + processing_times[j][s],
                name=f"tech_order_{j}_{s}"
            )

    # 2. Makespan definition: makespan >= completion of every job on last station
    for j in jobs:
        model.addConstr(
            makespan >= start[j][n_stations - 1] + processing_times[j][n_stations - 1],
            name=f"makespan_{j}"
        )

    # 3. Machine capacity: on each station, no two jobs overlap
    # Binary variable: order[j1][j2][s] = 1 if job j1 precedes job j2 on station s
    order = {}
    for s in stations:
        for j1 in jobs:
            for j2 in jobs:
                if j1 < j2:
                    order[j1, j2, s] = model.addVar(vtype=GRB.BINARY, name=f"order_{j1}_{j2}_{s}")

    for s in stations:
        for j1 in jobs:
            for j2 in jobs:
                if j1 < j2:
                    b = order[j1, j2, s]
                    # Either j1 finishes before j2 starts, or j2 finishes before j1 starts
                    model.addConstr(
                        start[j2][s] >= start[j1][s] + processing_times[j1][s] - M * (1 - b),
                        name=f"no_overlap_a_{j1}_{j2}_{s}"
                    )
                    model.addConstr(
                        start[j1][s] >= start[j2][s] + processing_times[j2][s] - M * b,
                        name=f"no_overlap_b_{j1}_{j2}_{s}"
                    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}