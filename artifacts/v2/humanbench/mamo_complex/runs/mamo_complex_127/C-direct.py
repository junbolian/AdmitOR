import gurobipy as gp
from gurobipy import GRB

def solve(params):
    initial_supply = params["initial_supply"]
    required_supply = params["required_supply"]

    # Find the cost matrix under whichever key it was stored
    cost_key = None
    for k in params:
        if k == "transfer_cost":
            cost_key = k
            break
    if cost_key is None:
        for k in params:
            if k not in ("initial_supply", "required_supply"):
                cost_key = k
                break
    transfer_cost = params[cost_key]

    n = len(initial_supply)
    facilities = range(n)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = {}
    for i in facilities:
        for j in facilities:
            if i != j:
                x[i, j] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")

    obj = gp.quicksum(transfer_cost[i][j] * x[i, j] for i in facilities for j in facilities if i != j)
    model.setObjective(obj, GRB.MINIMIZE)

    for i in facilities:
        inflow = gp.quicksum(x[j, i] for j in facilities if j != i)
        outflow = gp.quicksum(x[i, j] for j in facilities if j != i)
        model.addConstr(
            initial_supply[i] + inflow - outflow == required_supply[i],
            name=f"balance_{i}"
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