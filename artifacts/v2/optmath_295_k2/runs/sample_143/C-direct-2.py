import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    num_supply = 8
    num_demand = 7

    model = gp.Model("transportation")
    model.setParam("OutputFlag", 0)

    x = {}
    for i in range(num_supply):
        for j in range(num_demand):
            x[i, j] = model.addVar(
                lb=0.0,
                ub=capacity[i][j],
                vtype=GRB.CONTINUOUS,
                name=f"x_{i}_{j}"
            )

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(num_supply) for j in range(num_demand)),
        GRB.MINIMIZE
    )

    for i in range(num_supply):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_demand)) == supply[i],
            name=f"supply_{i}"
        )

    for j in range(num_demand):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_supply)) == demand[j],
            name=f"demand_{j}"
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