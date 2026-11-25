import gurobipy as gp
from gurobipy import GRB

def solve(params):
    durations = params["durations"]
    conflict_edges = params["conflict_edges"]

    n = len(durations)
    flights = list(range(n))

    # Upper bound on makespan: sum of all durations
    T = int(sum(durations))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Start times for each flight
    start = model.addVars(flights, lb=0, ub=T, vtype=GRB.CONTINUOUS, name="start")

    # Makespan variable
    makespan = model.addVar(lb=0, ub=T, vtype=GRB.CONTINUOUS, name="makespan")

    # Makespan >= start[i] + duration[i] for all i
    for i in flights:
        model.addConstr(makespan >= start[i] + durations[i], name=f"mksp_{i}")

    # For each conflict edge, the two flights must not overlap.
    # Either flight i finishes before flight j starts, or vice versa.
    # Introduce binary variable b[i,j]: b=1 means i before j, b=0 means j before i.
    b = {}
    for (i, j) in conflict_edges:
        b[(i, j)] = model.addVar(vtype=GRB.BINARY, name=f"b_{i}_{j}")
        # If b=1: start[i] + durations[i] <= start[j]
        model.addConstr(
            start[i] + durations[i] <= start[j] + T * (1 - b[(i, j)]),
            name=f"cf1_{i}_{j}"
        )
        # If b=0: start[j] + durations[j] <= start[i]
        model.addConstr(
            start[j] + durations[j] <= start[i] + T * b[(i, j)],
            name=f"cf2_{i}_{j}"
        )

    model.setObjective(makespan, GRB.MINIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}