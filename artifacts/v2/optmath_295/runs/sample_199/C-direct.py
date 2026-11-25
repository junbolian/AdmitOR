import gurobipy as gp
from gurobipy import GRB


def solve(params):
    net_supply = params["net_supply"]
    cost = params["cost"]
    capacity = params["capacity"]

    n = 9  # number of cities (structural constant)

    model = gp.Model("city_distribution")
    model.Params.OutputFlag = 0
    model.ModelSense = GRB.MINIMIZE

    # Decision variables: x[i,j] = flow from city i to city j (i != j)
    x = {}
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            x[i, j] = model.addVar(
                lb=0.0,
                ub=capacity[i][j],
                obj=cost[i][j],
                name=f"x_{i}_{j}",
            )

    # Flow balance: outflow - inflow = net_supply[i]
    # (positive net_supply => surplus city sends more than it receives)
    for i in range(n):
        outflow = gp.quicksum(x[i, j] for j in range(n) if j != i)
        inflow = gp.quicksum(x[j, i] for j in range(n) if j != i)
        model.addConstr(outflow - inflow == net_supply[i], name=f"balance_{i}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}