import gurobipy as gp
from gurobipy import GRB

def solve(params):
    d = [
        params["d1"],
        params["d2"],
        params["d3"],
        params["d4"],
        params["d5"],
        params["d6"],
        params["d7"],
    ]

    # x[i] = number of nurses starting their 5-consecutive-day shift on day i (1-indexed, cyclic week)
    # A nurse starting on day i works days i, i+1, i+2, i+3, i+4 (mod 7, 1-indexed)
    # There are 7 possible start days (one per day of the week)

    model = gp.Model("nurse_scheduling")
    model.setParam("OutputFlag", 0)

    # Continuous relaxation (no integrality)
    x = model.addVars(7, lb=0.0, name="x")

    # Objective: minimize total nurses
    model.setObjective(gp.quicksum(x[i] for i in range(7)), GRB.MINIMIZE)

    # Demand constraints: for each day j (0-indexed), the nurses covering it are those
    # who started on days j, j-1, j-2, j-3, j-4 (mod 7)
    for j in range(7):
        covering = [(j - k) % 7 for k in range(5)]
        model.addConstr(gp.quicksum(x[i] for i in covering) >= d[j], name=f"demand_day_{j+1}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        raw = model.ObjVal
        return {"objective": round(raw), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}