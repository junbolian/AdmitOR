import gurobipy as gp
from gurobipy import GRB


def solve(params):
    processing_times = params["processing_times"]
    num_jobs = params["num_jobs"]
    num_stations = params["num_stations"]

    # Big-M for disjunctive constraints
    M = sum(processing_times[j][s] for j in range(num_jobs) for s in range(num_stations))

    model = gp.Model("flowshop")
    model.setParam("OutputFlag", 0)

    # Start times: start[j][s] = start time of job j on station s
    start = [[model.addVar(lb=0.0, name=f"start_{j}_{s}")
              for s in range(num_stations)]
             for j in range(num_jobs)]

    # Makespan variable
    makespan = model.addVar(lb=0.0, name="makespan")

    # Objective: minimize makespan
    model.setObjective(makespan, GRB.MINIMIZE)

    # 1. Technological order: each job must finish on station s before starting station s+1
    for j in range(num_jobs):
        for s in range(num_stations - 1):
            model.addConstr(
                start[j][s + 1] >= start[j][s] + processing_times[j][s],
                name=f"tech_{j}_{s}"
            )

    # 2. No overlap on each station: for each pair of jobs, one must precede the other
    # Binary variable: order[j1][j2][s] = 1 if job j1 precedes job j2 on station s
    order = [[[None] * num_stations for _ in range(num_jobs)] for _ in range(num_jobs)]

    for s in range(num_stations):
        for j1 in range(num_jobs):
            for j2 in range(j1 + 1, num_jobs):
                y = model.addVar(vtype=GRB.BINARY, name=f"order_{j1}_{j2}_{s}")
                order[j1][j2][s] = y
                # If y=1: j1 before j2
                model.addConstr(
                    start[j2][s] >= start[j1][s] + processing_times[j1][s] - M * (1 - y),
                    name=f"seq1_{j1}_{j2}_{s}"
                )
                # If y=0: j2 before j1
                model.addConstr(
                    start[j1][s] >= start[j2][s] + processing_times[j2][s] - M * y,
                    name=f"seq2_{j1}_{j2}_{s}"
                )

    # 3. Makespan >= completion time of every job on last station
    last_station = num_stations - 1
    for j in range(num_jobs):
        model.addConstr(
            makespan >= start[j][last_station] + processing_times[j][last_station],
            name=f"mkspan_{j}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}