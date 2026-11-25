import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = params["capacity"]
    demand = params["demand"]
    min_delivery = params["min_delivery"]
    cost = params["cost"]

    num_producers = 3
    num_contracts = 4

    model = gp.Model("energy_allocation")
    model.Params.OutputFlag = 0

    x = model.addVars(num_producers, num_contracts, lb=0.0, vtype=GRB.CONTINUOUS, name="x")
    y = model.addVars(num_producers, num_contracts, vtype=GRB.BINARY, name="y")

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(num_producers) for j in range(num_contracts)),
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
            gp.quicksum(y[i, j] for i in range(num_producers)) >= 2,
            name=f"min_producers_{j}",
        )

    for i in range(num_producers):
        for j in range(num_contracts):
            model.addConstr(x[i, j] >= min_delivery[i] * y[i, j], name=f"min_del_{i}_{j}")
            model.addConstr(x[i, j] <= capacity[i] * y[i, j], name=f"link_{i}_{j}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}