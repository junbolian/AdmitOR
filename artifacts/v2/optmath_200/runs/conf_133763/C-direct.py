import gurobipy as gp
from gurobipy import GRB

def solve(params):
    value = params["value"]
    salary = params["salary"]
    budget = params["budget"]

    n = len(value)
    candidates = range(n)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(candidates, vtype=GRB.BINARY, name="x")

    model.setObjective(gp.quicksum(value[i] * x[i] for i in candidates), GRB.MAXIMIZE)

    model.addConstr(gp.quicksum(salary[i] * x[i] for i in candidates) <= budget, name="budget")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}