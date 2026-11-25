import gurobipy as gp
from gurobipy import GRB

def solve(params):
    durations = params["durations"]
    conflicts = params["conflicts"]

    n_flights = 8
    flights = list(range(n_flights))

    # Upper bound on makespan: sum of all durations
    T = sum(durations)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Start times for each flight
    start = model.addVars(flights, lb=0, ub=T, vtype=GRB.INTEGER, name="start")

    # Makespan variable
    makespan = model.addVar(lb=0, ub=T, vtype=GRB.INTEGER, name="makespan")

    # Makespan >= completion time of every flight
    for i in flights:
        model.addConstr(makespan >= start[i] + durations[i], name=f"mksp_{i}")

    # For each conflicting pair, one must finish before the other starts
    # Introduce binary variable: order[i,j] = 1 means i comes before j
    order = {}
    for idx, (i, j) in enumerate(conflicts):
        b = model.addVar(vtype=GRB.BINARY, name=f"order_{i}_{j}")
        order[(i, j)] = b
        # If b=1: start[j] >= start[i] + durations[i]
        # If b=0: start[i] >= start[j] + durations[j]
        model.addConstr(
            start[j] >= start[i] + durations[i] - T * (1 - b),
            name=f"conf_{i}_{j}_a"
        )
        model.addConstr(
            start[i] >= start[j] + durations[j] - T * b,
            name=f"conf_{i}_{j}_b"
        )

    model.setObjective(makespan, GRB.MINIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}