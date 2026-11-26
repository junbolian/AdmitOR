import gurobipy as gp
from gurobipy import GRB

def solve(params):
    a = params["a"]
    b = params["b"]
    n = len(a)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Landing times
    t = [model.addVar(lb=a[i], ub=b[i], name=f"t_{i}") for i in range(n)]

    # Minimum separation variable
    z = model.addVar(lb=0, name="z")

    # Maximize minimum separation
    model.setObjective(z, GRB.MAXIMIZE)

    # Flights land in order: t[i+1] - t[i] >= z for all consecutive pairs
    for i in range(n - 1):
        model.addConstr(t[i + 1] - t[i] >= z)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}