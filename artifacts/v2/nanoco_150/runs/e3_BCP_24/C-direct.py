import gurobipy as gp
from gurobipy import GRB

def solve(params):
    turnaround = params["turnaround"]

    # Dependency triplets with structure fixed, turnaround values from params
    dependencies_structure = [
        (0, 1), (0, 2), (0, 3), (0, 5), (0, 6), (0, 7),
        (1, 7), (2, 4), (2, 6), (2, 7), (3, 6), (4, 6), (4, 7), (5, 7)
    ]

    n_procs = 8
    n_deps = 14

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Upper bound on start times: sum of all turnaround values is a safe upper bound
    big_m = sum(turnaround) + n_procs

    # Start time variables (non-negative integers)
    start = model.addVars(n_procs, vtype=GRB.INTEGER, lb=0, ub=big_m, name="start")

    # Makespan variable
    makespan = model.addVar(vtype=GRB.INTEGER, lb=0, ub=big_m, name="makespan")

    # Makespan >= each start time
    for i in range(n_procs):
        model.addConstr(makespan >= start[i], name=f"mks_{i}")

    # For each dependency, |start[u] - start[v]| >= d
    # Linearize with binary variable: b=1 means start[u] - start[v] >= d, b=0 means start[v] - start[u] >= d
    b = model.addVars(n_deps, vtype=GRB.BINARY, name="b")

    for k in range(n_deps):
        u, v = dependencies_structure[k]
        d = turnaround[k]
        # If b[k] = 1: start[u] - start[v] >= d
        # If b[k] = 0: start[v] - start[u] >= d
        model.addConstr(
            start[u] - start[v] >= d - big_m * (1 - b[k]),
            name=f"dep_ab_{k}"
        )
        model.addConstr(
            start[v] - start[u] >= d - big_m * b[k],
            name=f"dep_ba_{k}"
        )

    model.setObjective(makespan, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(makespan.X), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}