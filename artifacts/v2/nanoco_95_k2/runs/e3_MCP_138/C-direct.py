import gurobipy as gp
from gurobipy import GRB

def solve(params):
    durations = params["durations"]
    conflict_edges = params["conflict_edges"]

    n_flights = 8
    flights = range(n_flights)

    # Big-M: upper bound on makespan (sum of all durations is safe)
    M = sum(durations[i] for i in flights)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Start time for each flight
    start = model.addVars(flights, lb=0.0, name="start")

    # Makespan variable
    makespan = model.addVar(lb=0.0, name="makespan")

    # Makespan >= start[i] + duration[i] for all i
    for i in flights:
        model.addConstr(makespan >= start[i] + durations[i])

    # For each conflict edge, one flight must finish before the other starts.
    # Introduce binary variable b[i,j]: 1 => i before j, 0 => j before i
    b = {}
    for (i, j) in conflict_edges:
        b[(i, j)] = model.addVar(vtype=GRB.BINARY, name=f"b_{i}_{j}")
        # If b=1: start[i] + durations[i] <= start[j]
        model.addConstr(start[i] + durations[i] <= start[j] + M * (1 - b[(i, j)]))
        # If b=0: start[j] + durations[j] <= start[i]
        model.addConstr(start[j] + durations[j] <= start[i] + M * b[(i, j)])

    model.setObjective(makespan, GRB.MINIMIZE)
    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(makespan.X), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}