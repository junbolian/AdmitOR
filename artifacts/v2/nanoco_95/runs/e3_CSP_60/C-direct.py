import gurobipy as gp
from gurobipy import GRB
from itertools import product

def solve(params):
    bolt_length = params["bolt_length"]
    strip_lengths = params["strip_lengths"]
    demands = params["demands"]

    n = len(strip_lengths)

    max_counts = [int(bolt_length // strip_lengths[i]) for i in range(n)]

    patterns = []
    ranges = [range(mc + 1) for mc in max_counts]
    for combo in product(*ranges):
        total = sum(combo[i] * strip_lengths[i] for i in range(n))
        if 0 < total <= bolt_length:
            patterns.append(list(combo))

    model = gp.Model("cutting_stock")
    model.Params.OutputFlag = 0

    num_patterns = len(patterns)
    x = model.addVars(num_patterns, vtype=GRB.INTEGER, lb=0, name="x")

    model.setObjective(gp.quicksum(x[p] for p in range(num_patterns)), GRB.MINIMIZE)

    for i in range(n):
        model.addConstr(
            gp.quicksum(patterns[p][i] * x[p] for p in range(num_patterns)) >= demands[i],
            name=f"demand_{i}"
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.objVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}