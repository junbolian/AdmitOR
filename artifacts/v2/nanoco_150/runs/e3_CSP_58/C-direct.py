import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    stock_length = params["stock_length"]
    segment_lengths = params["segment_lengths"]
    demands = params["demands"]

    n_types = len(segment_lengths)

    # Enumerate all feasible cutting patterns
    # A pattern is a tuple (x0, x1, ..., x_{n-1}) where xi >= 0 integers
    # and sum(xi * segment_lengths[i]) <= stock_length

    patterns = []
    max_cuts = [int(stock_length // segment_lengths[i]) for i in range(n_types)]

    ranges = [range(0, max_cuts[i] + 1) for i in range(n_types)]
    for combo in itertools.product(*ranges):
        if sum(combo[i] * segment_lengths[i] for i in range(n_types)) <= stock_length:
            patterns.append(combo)

    n_patterns = len(patterns)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[p] = number of reels cut using pattern p (integer)
    x = model.addVars(n_patterns, vtype=GRB.INTEGER, lb=0, name="x")

    # Minimize total reels used
    model.setObjective(gp.quicksum(x[p] for p in range(n_patterns)), GRB.MINIMIZE)

    # Demand constraints: each segment type must be met exactly
    for i in range(n_types):
        model.addConstr(
            gp.quicksum(patterns[p][i] * x[p] for p in range(n_patterns)) >= demands[i],
            name=f"demand_{i}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}