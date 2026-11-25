import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    min_producers = params["min_producers"]
    min_delivery = params["min_delivery"]

    num_producers = 4
    num_contracts = 5

    model = gp.Model("energy_production")
    model.Params.OutputFlag = 0

    x = {}
    y = {}
    for i in range(num_producers):
        for j in range(num_contracts):
            x[i, j] = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")
            y[i, j] = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{j}")

    model.update()

    model.setObjective(
        gp.quicksum(
            cost[i][j] * x[i, j]
            for i in range(num_producers)
            for j in range(num_contracts)
        ),
        GRB.MINIMIZE,
    )

    for i in range(num_producers):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_contracts)) <= capacity[i],
            name=f"capacity_{i}",
        )

    for j in range(num_contracts):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_producers)) >= demand[j],
            name=f"demand_{j}",
        )

    for j in range(num_contracts):
        model.addConstr(
            gp.quicksum(y[i, j] for i in range(num_producers)) >= min_producers[j],
            name=f"min_producers_{j}",
        )

    for i in range(num_producers):
        for j in range(num_contracts):
            model.addConstr(
                x[i, j] >= min_delivery[i] * y[i, j],
                name=f"min_deliver_{i}_{j}",
            )
            model.addConstr(
                x[i, j] <= capacity[i] * y[i, j],
                name=f"link_{i}_{j}",
            )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}