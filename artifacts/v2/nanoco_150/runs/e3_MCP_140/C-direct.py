import gurobipy as gp
from gurobipy import GRB

def solve(params):
    durations = params["durations"]
    conflict_pairs = params["conflict_pairs"]

    n = 8
    # Upper bound on makespan: sum of all durations
    T = sum(durations)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Start times for each robot
    start = [model.addVar(lb=0, ub=T, vtype=GRB.INTEGER, name=f"start_{i}") for i in range(n)]

    # Makespan variable
    makespan = model.addVar(lb=0, ub=T, vtype=GRB.INTEGER, name="makespan")

    # Each robot's interval ends at start[i] + durations[i]; makespan >= all end times
    for i in range(n):
        model.addConstr(makespan >= start[i] + durations[i], name=f"mkspan_{i}")

    # For each conflict pair, one robot must finish before the other starts
    # Introduce binary variable b[k]: if 1, robot i finishes before robot j starts; else robot j before robot i
    b = []
    for k, (i, j) in enumerate(conflict_pairs):
        bvar = model.addVar(vtype=GRB.BINARY, name=f"b_{k}")
        b.append(bvar)
        # If bvar=1: start[i] + durations[i] <= start[j]
        # If bvar=0: start[j] + durations[j] <= start[i]
        model.addConstr(
            start[i] + durations[i] <= start[j] + T * (1 - bvar),
            name=f"conflict_{k}_a"
        )
        model.addConstr(
            start[j] + durations[j] <= start[i] + T * bvar,
            name=f"conflict_{k}_b"
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