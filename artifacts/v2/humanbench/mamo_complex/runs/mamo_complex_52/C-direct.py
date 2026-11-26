import gurobipy as gp
from gurobipy import GRB

def solve(params):
    d = params["d"]  # list or dict of demand for each day, indexed 0..6 or 1..7

    # Normalize demand to 0-indexed list of length 7
    if isinstance(d, dict):
        demand = [d[j] for j in sorted(d.keys())]
    else:
        demand = list(d)

    # There are 7 possible start days (nurses starting on day 1..7, working 5 consecutive days)
    # x[i] = number of nurses starting their 5-day block on day i (0-indexed: i = 0..6)
    # A nurse starting on day i works days i, i+1, i+2, i+3, i+4 (mod 7)

    model = gp.Model("nurse_scheduling")
    model.setParam("OutputFlag", 0)

    # Decision variables (continuous relaxation)
    x = model.addVars(7, lb=0.0, name="x")

    # Objective: minimize total nurses
    model.setObjective(gp.quicksum(x[i] for i in range(7)), GRB.MINIMIZE)

    # Demand constraints: for each day j, sum of nurses working on day j >= d[j]
    for j in range(7):
        # Nurses working on day j are those who started on day i such that
        # j is in {i, i+1, i+2, i+3, i+4} mod 7
        # Equivalently, i in {j, j-1, j-2, j-3, j-4} mod 7
        workers = gp.quicksum(x[(j - k) % 7] for k in range(5))
        model.addConstr(workers >= demand[j], name=f"demand_day_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        obj_val = model.ObjVal
        # Round to nearest integer as specified
        rounded = round(obj_val)
        return {"objective": float(rounded), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}