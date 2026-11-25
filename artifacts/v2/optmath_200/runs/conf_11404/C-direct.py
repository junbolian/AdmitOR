import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 13
    values = [params[f"value_{i}"] for i in range(n)]
    costs = [params[f"cost_{i}"] for i in range(n)]
    budget = params["budget"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n, vtype=GRB.BINARY, name="x")

    model.setObjective(gp.quicksum(values[i] * x[i] for i in range(n)), GRB.MAXIMIZE)
    model.addConstr(gp.quicksum(costs[i] * x[i] for i in range(n)) <= budget, name="budget")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}