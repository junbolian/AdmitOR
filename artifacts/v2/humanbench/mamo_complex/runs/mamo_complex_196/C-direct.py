import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = params["n"]
    a = params["a"]  # list of earliest landing times, length n
    b = params["b"]  # list of latest landing times, length n

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Landing times for each flight
    t = [model.addVar(lb=a[i], ub=b[i], name=f"t_{i}") for i in range(n)]

    # Minimum separation variable
    delta = model.addVar(lb=0.0, name="delta")

    # Flights must land in order 1..n, so t[i] <= t[i+1]
    # Separation between consecutive landings >= delta
    for i in range(n - 1):
        model.addConstr(t[i + 1] - t[i] >= delta, name=f"sep_{i}")

    # Maximize minimum separation
    model.setObjective(delta, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": round(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}