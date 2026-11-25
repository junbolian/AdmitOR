import gurobipy as gp
from gurobipy import GRB

def solve(params):
    processing_time = params["processing_time"]

    n_batches = 3
    n_stations = 3
    batches = range(n_batches)
    stations = range(n_stations)

    # Big-M for disjunctive constraints
    M = sum(processing_time[i][j] for i in batches for j in stations) + 1

    model = gp.Model("flowshop")
    model.setParam("OutputFlag", 0)

    # Start times: start[i][j] = start time of batch i on station j
    start = [[model.addVar(lb=0.0, name=f"start_{i}_{j}") for j in stations] for i in batches]

    # Makespan variable
    makespan = model.addVar(lb=0.0, name="makespan")

    # Objective: minimize makespan
    model.setObjective(makespan, GRB.MINIMIZE)

    # 1. Stage precedence: batch i must finish station j before starting station j+1
    for i in batches:
        for j in range(n_stations - 1):
            model.addConstr(
                start[i][j + 1] >= start[i][j] + processing_time[i][j],
                name=f"stage_prec_{i}_{j}"
            )

    # 2. Machine disjunctive constraints: on each station, no two batches overlap
    # Binary variable y[i][k][j] = 1 if batch i precedes batch k on station j
    y = {}
    for j in stations:
        for i in batches:
            for k in batches:
                if i < k:
                    y[i, k, j] = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{k}_{j}")

    for j in stations:
        for i in batches:
            for k in batches:
                if i < k:
                    # Either i finishes before k starts, or k finishes before i starts
                    model.addConstr(
                        start[k][j] >= start[i][j] + processing_time[i][j] - M * (1 - y[i, k, j]),
                        name=f"disj1_{i}_{k}_{j}"
                    )
                    model.addConstr(
                        start[i][j] >= start[k][j] + processing_time[k][j] - M * y[i, k, j],
                        name=f"disj2_{i}_{k}_{j}"
                    )

    # 3. Makespan >= completion time of every batch on station 2
    for i in batches:
        model.addConstr(
            makespan >= start[i][2] + processing_time[i][2],
            name=f"makespan_{i}"
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