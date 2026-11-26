import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]  # list of 7 values, demand[j] for day j+1

    # There are 7 possible shift patterns (each nurse works 5 consecutive days).
    # Pattern i: nurse starts on day i (1-indexed), works days i, i+1, i+2, i+3, i+4 (mod 7, 1-indexed).
    # x[i] = number of nurses starting their 5-day block on day i, i = 0..6 (0-indexed start day)

    num_days = 7
    num_patterns = 7  # one start day per day of the week

    # Build coverage matrix: A[j][i] = 1 if pattern i covers day j
    # Pattern i covers days i, (i+1)%7, (i+2)%7, (i+3)%7, (i+4)%7
    A = []
    for j in range(num_days):
        row = []
        for i in range(num_patterns):
            covers = any((i + k) % num_days == j for k in range(5))
            row.append(1 if covers else 0)
        A.append(row)

    model = gp.Model("nurse_scheduling")
    model.setParam("OutputFlag", 0)

    # Continuous relaxation (no integrality)
    x = model.addVars(num_patterns, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    # Minimize total nurses
    model.setObjective(gp.quicksum(x[i] for i in range(num_patterns)), GRB.MINIMIZE)

    # Demand constraints for each day
    for j in range(num_days):
        model.addConstr(
            gp.quicksum(A[j][i] * x[i] for i in range(num_patterns)) >= demand[j],
            name=f"demand_day_{j}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        obj_val = model.ObjVal
        # Round to nearest integer as specified
        return {"objective": round(obj_val), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}