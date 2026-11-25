import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    standard_length = params["standard_rebar_length"]
    demand_18 = params["demand_18"]
    demand_20 = params["demand_20"]
    demand_56 = params["demand_56"]
    L18 = params["piece_length_18"]
    L20 = params["piece_length_20"]
    L56 = params["piece_length_56"]

    # Enumerate all feasible cutting patterns (non-negative integer combos that fit in one rebar)
    patterns = []
    max_18 = int(standard_length // L18)
    max_20 = int(standard_length // L20)
    max_56 = int(standard_length // L56)

    for n18 in range(max_18 + 1):
        for n20 in range(max_20 + 1):
            for n56 in range(max_56 + 1):
                if n18 == 0 and n20 == 0 and n56 == 0:
                    continue
                if n18 * L18 + n20 * L20 + n56 * L56 <= standard_length:
                    patterns.append((n18, n20, n56))

    if not patterns:
        return {"objective": None, "status": "no_feasible_patterns"}

    num_patterns = len(patterns)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[j] = number of times pattern j is used (integer)
    x = model.addVars(num_patterns, vtype=GRB.INTEGER, lb=0, name="x")

    # Minimize total rebars used
    model.setObjective(gp.quicksum(x[j] for j in range(num_patterns)), GRB.MINIMIZE)

    # Demand constraints
    model.addConstr(
        gp.quicksum(patterns[j][0] * x[j] for j in range(num_patterns)) >= demand_18,
        name="demand18"
    )
    model.addConstr(
        gp.quicksum(patterns[j][1] * x[j] for j in range(num_patterns)) >= demand_20,
        name="demand20"
    )
    model.addConstr(
        gp.quicksum(patterns[j][2] * x[j] for j in range(num_patterns)) >= demand_56,
        name="demand56"
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