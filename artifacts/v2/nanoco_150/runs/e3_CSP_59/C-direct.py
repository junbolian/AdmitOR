import gurobipy as gp
from gurobipy import GRB
from itertools import product as iproduct


def solve(params):
    bar_length = params["bar_length"]
    order_28 = params["order_28"]
    order_38 = params["order_38"]
    order_21 = params["order_21"]
    piece_length_28 = params["piece_length_28"]
    piece_length_38 = params["piece_length_38"]
    piece_length_21 = params["piece_length_21"]

    # Enumerate all feasible cutting patterns (non-negative integer combos that fit in one bar)
    patterns = []
    max_28 = int(bar_length // piece_length_28)
    max_38 = int(bar_length // piece_length_38)
    max_21 = int(bar_length // piece_length_21)

    for n28 in range(max_28 + 1):
        for n38 in range(max_38 + 1):
            for n21 in range(max_21 + 1):
                used = n28 * piece_length_28 + n38 * piece_length_38 + n21 * piece_length_21
                if used <= bar_length and (n28 + n38 + n21) > 0:
                    patterns.append((n28, n38, n21))

    if not patterns:
        return {"objective": None, "status": "no feasible patterns"}

    num_patterns = len(patterns)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[j] = number of bars cut using pattern j (integer)
    x = model.addVars(num_patterns, vtype=GRB.INTEGER, lb=0, name="x")

    # Minimize total bars used
    model.setObjective(gp.quicksum(x[j] for j in range(num_patterns)), GRB.MINIMIZE)

    # Demand constraints: each segment type must be met exactly
    model.addConstr(
        gp.quicksum(patterns[j][0] * x[j] for j in range(num_patterns)) >= order_28,
        name="demand_28"
    )
    model.addConstr(
        gp.quicksum(patterns[j][1] * x[j] for j in range(num_patterns)) >= order_38,
        name="demand_38"
    )
    model.addConstr(
        gp.quicksum(patterns[j][2] * x[j] for j in range(num_patterns)) >= order_21,
        name="demand_21"
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