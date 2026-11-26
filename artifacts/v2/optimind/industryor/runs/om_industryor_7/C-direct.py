import gurobipy as gp
from gurobipy import GRB

def solve(params):
    workers = ["I", "II", "III", "IV", "V"]
    tasks = ["A", "B", "C", "D"]

    # Build cost matrix from params
    cost = {
        (w, t): params[f"time_{w}_{t}"]
        for w in workers
        for t in tasks
    }

    model = gp.Model("assignment")
    model.setParam("OutputFlag", 0)

    # Binary assignment variables: x[w, t] = 1 if worker w is assigned to task t
    x = model.addVars(workers, tasks, vtype=GRB.BINARY, name="x")

    # Objective: minimize total hours
    model.setObjective(
        gp.quicksum(cost[w, t] * x[w, t] for w in workers for t in tasks),
        GRB.MINIMIZE
    )

    # Each task must be assigned to exactly one worker
    for t in tasks:
        model.addConstr(
            gp.quicksum(x[w, t] for w in workers) == 1,
            name=f"task_{t}"
        )

    # Each worker can be assigned to at most one task (4 out of 5 workers are used)
    for w in workers:
        model.addConstr(
            gp.quicksum(x[w, t] for t in tasks) <= 1,
            name=f"worker_{w}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}