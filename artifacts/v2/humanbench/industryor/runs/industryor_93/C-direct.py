import gurobipy as gp
from gurobipy import GRB
import math

def solve(params):
    stock_3m_count = params["stock_3m_count"]
    stock_4m_count = params["stock_4m_count"]
    raw_length = params["raw_length"]
    piece_3m_length = params["piece_3m_length"]
    piece_4m_length = params["piece_4m_length"]

    # Enumerate all feasible cutting patterns:
    # Each pattern (a, b) means cutting 'a' pieces of piece_3m_length and 'b' pieces of piece_4m_length
    # from one raw rebar of raw_length, with no waste exceeding one piece.
    patterns = []
    max_3m = int(raw_length // piece_3m_length)
    max_4m = int(raw_length // piece_4m_length)

    for a in range(max_3m + 1):
        for b in range(max_4m + 1):
            if a * piece_3m_length + b * piece_4m_length <= raw_length:
                patterns.append((a, b))

    # Remove the trivial (0, 0) pattern since it wastes an entire rebar
    patterns = [(a, b) for a, b in patterns if a + b > 0]

    num_patterns = len(patterns)

    model = gp.Model("rebar_cutting")
    model.setParam("OutputFlag", 0)

    # x[j] = number of raw rebars cut using pattern j (integer)
    x = model.addVars(num_patterns, vtype=GRB.INTEGER, lb=0, name="x")

    # Objective: minimize total number of raw rebars used
    model.setObjective(gp.quicksum(x[j] for j in range(num_patterns)), GRB.MINIMIZE)

    # Demand constraints:
    # Total 3m pieces produced >= stock_3m_count
    model.addConstr(
        gp.quicksum(patterns[j][0] * x[j] for j in range(num_patterns)) >= stock_3m_count,
        name="demand_3m"
    )

    # Total 4m pieces produced >= stock_4m_count
    model.addConstr(
        gp.quicksum(patterns[j][1] * x[j] for j in range(num_patterns)) >= stock_4m_count,
        name="demand_4m"
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