import gurobipy as gp
from gurobipy import GRB

def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    cost = params["cost"]
    pair_cap = params["pair_cap"]

    n_people = len(availability)
    n_projects = len(demand)

    model = gp.Model("workforce_allocation")
    model.setParam("OutputFlag", 0)

    x = {}
    for i in range(n_people):
        for j in range(n_projects):
            x[i, j] = model.addVar(
                lb=0,
                ub=pair_cap[i][j],
                obj=cost[i][j],
                name=f"x_{i}_{j}",
            )

    model.modelSense = GRB.MINIMIZE

    for i in range(n_people):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_projects)) <= availability[i],
            name=f"availability_{i}",
        )

    for j in range(n_projects):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_people)) >= demand[j],
            name=f"demand_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}