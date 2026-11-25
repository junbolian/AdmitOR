import gurobipy as gp
from gurobipy import GRB


def solve(params):
    durations = params["durations"]

    n = 8
    edges = [(0, 1), (2, 4), (2, 7), (3, 7), (1, 4),
             (2, 3), (0, 5), (2, 5), (3, 5)]

    # Big-M: any feasible schedule fits within the sum of all durations
    # (sequential placement is always feasible), so this upper-bounds e_i - s_j.
    M = sum(durations) + 1

    model = gp.Model("timeslot_allocation")
    model.Params.OutputFlag = 0

    # Start time of each device's contiguous interval.
    s = model.addVars(n, lb=0.0, vtype=GRB.CONTINUOUS, name="s")
    # Horizon (latest closing time) to minimize.
    T = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="T")
    # Ordering binary for each interference edge:
    #   y[k] = 1  -> device i finishes before device j starts
    #   y[k] = 0  -> device j finishes before device i starts
    y = model.addVars(len(edges), vtype=GRB.BINARY, name="y")

    # Each device's interval end time must not exceed the horizon.
    for i in range(n):
        model.addConstr(s[i] + durations[i] <= T, name="horizon_%d" % i)

    # Non-overlap disjunction for each interference coupling.
    for k, (i, j) in enumerate(edges):
        model.addConstr(s[i] + durations[i] <= s[j] + M * (1 - y[k]),
                        name="before_%d" % k)
        model.addConstr(s[j] + durations[j] <= s[i] + M * y[k],
                        name="after_%d" % k)

    model.setObjective(T, GRB.MINIMIZE)
    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(T.X), "status": "optimal"}
    return {"objective": None, "status": "failed"}