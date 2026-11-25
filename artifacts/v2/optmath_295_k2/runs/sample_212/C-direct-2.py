import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_margins = params["profit_margins"]
    resource_consumption = params["resource_consumption"]
    resource_budget = params["resource_budget"]
    production_capacities = params["production_capacities"]

    n_items = 43

    model = gp.Model("manufacturing")
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_items, lb=0.0, name="x")

    for i in range(n_items):
        x[i].ub = production_capacities[i]

    model.setObjective(
        gp.quicksum(profit_margins[i] * x[i] for i in range(n_items)),
        GRB.MAXIMIZE
    )

    model.addConstr(
        gp.quicksum(resource_consumption[i] * x[i] for i in range(n_items)) <= resource_budget,
        name="resource_budget"
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