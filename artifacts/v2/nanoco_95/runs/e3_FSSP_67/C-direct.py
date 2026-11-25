import gurobipy as gp
from gurobipy import GRB


def solve(params):
    processing_times = params["processing_times"]
    num_stations = params["num_stations"]
    num_batches = params["num_batches"]

    # processing_times may be flat (batch-major) or nested list-of-lists
    if isinstance(processing_times[0], (list, tuple)):
        p = [[processing_times[b][s] for s in range(num_stations)] for b in range(num_batches)]
    else:
        p = [[processing_times[b * num_stations + s] for s in range(num_stations)] for b in range(num_batches)]

    batches = range(num_batches)
    stations = range(num_stations)

    model = gp.Model("flowshop")
    model.setParam("OutputFlag", 0)

    # Start times: start[b][s] = start time of batch b on station s
    start = [[model.addVar(lb=0.0, name=f"start_{b}_{s}") for s in stations] for b in batches]

    # Makespan variable
    makespan = model.addVar(lb=0.0, name="makespan")

    # Objective: minimize makespan
    model.setObjective(makespan, GRB.MINIMIZE)

    # Makespan >= completion of every batch on the last station
    last_s = num_stations - 1
    for b in batches:
        model.addConstr(makespan >= start[b][last_s] + p[b][last_s], name=f"mkspan_{b}")

    # Stage precedence: batch b must finish station s before starting station s+1
    for b in batches:
        for s in range(num_stations - 1):
            model.addConstr(start[b][s + 1] >= start[b][s] + p[b][s], name=f"seq_{b}_{s}")

    # Machine capacity: no two batches can overlap on the same station
    # Binary variable y[b1][b2][s] = 1 if batch b1 precedes batch b2 on station s
    M = sum(p[b][s] for b in batches for s in stations) + 1  # big-M

    y = {}
    for b1 in batches:
        for b2 in batches:
            if b1 < b2:
                for s in stations:
                    y[b1, b2, s] = model.addVar(vtype=GRB.BINARY, name=f"y_{b1}_{b2}_{s}")

    for b1 in batches:
        for b2 in batches:
            if b1 < b2:
                for s in stations:
                    # Either b1 finishes before b2 starts, or b2 finishes before b1 starts
                    model.addConstr(
                        start[b2][s] >= start[b1][s] + p[b1][s] - M * (1 - y[b1, b2, s]),
                        name=f"order1_{b1}_{b2}_{s}"
                    )
                    model.addConstr(
                        start[b1][s] >= start[b2][s] + p[b2][s] - M * y[b1, b2, s],
                        name=f"order2_{b1}_{b2}_{s}"
                    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}