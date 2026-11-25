import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    min_contributors = params["min_contributors"]
    min_delivery = params["min_delivery"]

    P = len(capacity)
    C = len(demand)

    model = gp.Model("energy_allocation")
    model.Params.OutputFlag = 0

    x = {}
    y = {}
    for i in range(P):
        for j in range(C):
            x[i, j] = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")
            y[i, j] = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{j}")

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(P) for j in range(C)),
        GRB.MINIMIZE,
    )

    for i in range(P):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(C)) <= capacity[i],
            name=f"cap_{i}",
        )

    for j in range(C):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(P)) >= demand[j],
            name=f"demand_{j}",
        )

    for j in range(C):
        model.addConstr(
            gp.quicksum(y[i, j] for i in range(P)) >= min_contributors[j],
            name=f"mincontrib_{j}",
        )

    for i in range(P):
        for j in range(C):
            model.addConstr(
                x[i, j] <= capacity[i] * y[i, j],
                name=f"link_up_{i}_{j}",
            )
            model.addConstr(
                x[i, j] >= min_delivery[i] * y[i, j],
                name=f"link_lo_{i}_{j}",
            )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}