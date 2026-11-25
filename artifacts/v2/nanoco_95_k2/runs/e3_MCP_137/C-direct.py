import gurobipy as gp
from gurobipy import GRB

def solve(params):
    durations = params["durations"]
    n = 8
    edges = [(0,1),(2,4),(2,7),(3,7),(1,4),(2,3),(0,5),(2,5),(3,5)]

    # Upper bound on makespan: sum of all durations
    total = sum(durations)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # start[i] = start time of device i
    start = model.addVars(n, lb=0, ub=total, vtype=GRB.INTEGER, name="start")
    makespan = model.addVar(lb=0, ub=total, vtype=GRB.INTEGER, name="makespan")

    # makespan >= start[i] + duration[i] for all i
    for i in range(n):
        model.addConstr(makespan >= start[i] + durations[i])

    # For each interference edge (i, j), intervals must not overlap.
    # Either i finishes before j starts, or j finishes before i starts.
    # Introduce binary variable b[i,j]: 1 if i is scheduled before j, 0 otherwise.
    b = {}
    for (i, j) in edges:
        b[i, j] = model.addVar(vtype=GRB.BINARY, name=f"b_{i}_{j}")
        # If b[i,j] = 1: start[i] + durations[i] <= start[j]
        # If b[i,j] = 0: start[j] + durations[j] <= start[i]
        M = total
        model.addConstr(start[i] + durations[i] <= start[j] + M * (1 - b[i, j]))
        model.addConstr(start[j] + durations[j] <= start[i] + M * b[i, j])

    model.setObjective(makespan, GRB.MINIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(makespan.X), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}