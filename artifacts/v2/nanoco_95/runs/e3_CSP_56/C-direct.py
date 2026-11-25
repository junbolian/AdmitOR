import gurobipy as gp
from gurobipy import GRB
from itertools import product as iproduct


def solve(params):
    segment_lengths = params["segment_lengths"]
    segment_demands = params["segment_demands"]
    standard_rebar_length = params["standard_rebar_length"]

    n_types = len(segment_lengths)

    # Enumerate all feasible cutting patterns:
    # a pattern is a tuple (c_0, c_1, ..., c_{n-1}) where c_i is the count
    # of segment type i cut from one rebar, subject to sum(c_i * l_i) <= L
    max_counts = [int(standard_rebar_length // segment_lengths[i]) for i in range(n_types)]

    patterns = []
    ranges = [range(0, max_counts[i] + 1) for i in range(n_types)]
    for combo in iproduct(*ranges):
        used = sum(combo[i] * segment_lengths[i] for i in range(n_types))
        if used <= standard_rebar_length and sum(combo) > 0:
            patterns.append(combo)

    if not patterns:
        return {"objective": None, "status": "no_feasible_patterns"}

    n_patterns = len(patterns)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[j] = number of rebars cut according to pattern j (integer)
    x = model.addVars(n_patterns, vtype=GRB.INTEGER, lb=0, name="x")

    # Minimize total rebars used
    model.setObjective(gp.quicksum(x[j] for j in range(n_patterns)), GRB.MINIMIZE)

    # Demand constraints: each segment type must meet its required quantity
    for i in range(n_types):
        model.addConstr(
            gp.quicksum(patterns[j][i] * x[j] for j in range(n_patterns)) >= segment_demands[i],
            name=f"demand_{i}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}