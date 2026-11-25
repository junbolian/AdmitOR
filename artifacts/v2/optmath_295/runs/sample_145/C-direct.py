import gurobipy as gp
from gurobipy import GRB

def solve(params):
    educational_value = params["educational_value"]
    cost = params["cost"]
    budget = params["budget"]

    n = len(educational_value)
    resources = range(n)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(resources, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(educational_value[i] * x[i] for i in resources),
        GRB.MAXIMIZE
    )

    model.addConstr(
        gp.quicksum(cost[i] * x[i] for i in resources) <= budget,
        name="budget"
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