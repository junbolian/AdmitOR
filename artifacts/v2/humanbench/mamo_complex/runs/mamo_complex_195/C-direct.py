import gurobipy as gp
from gurobipy import GRB

def solve(params):
    days = [1, 2, 3, 4, 5, 6, 7]
    demand = {j: params[f"d{j}"] for j in days}

    model = gp.Model("nurse_schedule")
    model.Params.OutputFlag = 0

    # x[s]: number of nurses starting their 5-day shift block on day s
    x = model.addVars(days, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    # Each nurse works 5 consecutive days starting on day s, then rests 2 days
    model.setObjective(gp.quicksum(x[s] for s in days), GRB.MINIMIZE)

    for j in days:
        covered = gp.quicksum(
            x[s] for s in days if any((s + k - 1) % 7 + 1 == j for k in range(5))
        )
        model.addConstr(covered >= demand[j], name=f"demand_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": "no_optimal_solution"}