import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_facilities = len(supply)
    n_centers = len(demand)

    model = gp.Model("transportation")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(n_facilities):
        for j in range(n_centers):
            x[i, j] = model.addVar(
                lb=0,
                ub=capacity[i][j],
                obj=cost[i][j],
                name=f"x_{i}_{j}"
            )

    model.modelSense = GRB.MINIMIZE

    for i in range(n_facilities):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_centers)) == supply[i],
            name=f"supply_{i}"
        )

    for j in range(n_centers):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_facilities)) == demand[j],
            name=f"demand_{j}"
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": "infeasible"}