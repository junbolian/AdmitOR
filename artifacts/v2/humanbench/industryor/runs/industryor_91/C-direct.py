import gurobipy as gp
from gurobipy import GRB

def solve(params):
    req_1 = params["req_1"]
    req_2 = params["req_2"]
    req_3 = params["req_3"]
    req_4 = params["req_4"]
    req_5 = params["req_5"]
    req_6 = params["req_6"]
    shift_length = params["shift_length"]

    # Each shift is 4 hours; workers start at beginning of a shift and work
    # continuously for shift_length hours (default 8 = 2 consecutive shifts).
    # Number of consecutive shifts covered = shift_length / 4
    period_duration = 4  # hours per period
    spans = int(round(shift_length / period_duration))  # how many periods one worker covers

    # x[i] = number of workers starting at the beginning of shift i (1-indexed)
    # There are 6 shifts arranged cyclically.
    num_shifts = 6

    model = gp.Model("bus_crew_scheduling")
    model.setParam("OutputFlag", 0)

    x = model.addVars(range(1, num_shifts + 1), vtype=GRB.INTEGER, lb=0, name="x")

    # Objective: minimize total workers
    model.setObjective(gp.quicksum(x[i] for i in range(1, num_shifts + 1)), GRB.MINIMIZE)

    # Requirements: during shift p, all workers who started in the previous
    # (spans) shifts (cyclically) are still working.
    requirements = {1: req_1, 2: req_2, 3: req_3, 4: req_4, 5: req_5, 6: req_6}

    for p in range(1, num_shifts + 1):
        # Workers active during shift p are those who started at shifts
        # p, p-1, ..., p-(spans-1)  (mod 6, 1-indexed)
        covering = gp.LinExpr()
        for k in range(spans):
            start_shift = ((p - 1 - k) % num_shifts) + 1
            covering += x[start_shift]
        model.addConstr(covering >= requirements[p], name=f"req_shift_{p}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}