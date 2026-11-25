import gurobipy as gp
from gurobipy import GRB


def solve(params):
    capacity = params["capacity"]
    demand = params["demand"]
    min_delivery = params["min_delivery"]
    cost = params["cost"]

    n_producers = len(capacity)
    n_contracts = len(demand)

    model = gp.Model("energy_allocation")
    model.Params.OutputFlag = 0

    # x[i, j]: units producer i delivers to contract j
    x = {}
    for i in range(n_producers):
        for j in range(n_contracts):
            x[i, j] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")

    # y[i, j]: 1 if producer i contributes to contract j
    y = {}
    for i in range(n_producers):
        for j in range(n_contracts):
            y[i, j] = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{j}")

    model.update()

    # Objective: minimize total production cost
    model.setObjective(
        gp.quicksum(
            cost[i][j] * x[i, j]
            for i in range(n_producers)
            for j in range(n_contracts)
        ),
        GRB.MINIMIZE,
    )

    # Capacity: total allocation by a producer across contracts <= capacity[i]
    for i in range(n_producers):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_contracts)) <= capacity[i],
            name=f"capacity_{i}",
        )

    # Contract fulfillment: total allocation to a contract >= demand[j]
    for j in range(n_contracts):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_producers)) >= demand[j],
            name=f"demand_{j}",
        )

    # Minimum contributors: at least 2 producers per contract
    for j in range(n_contracts):
        model.addConstr(
            gp.quicksum(y[i, j] for i in range(n_producers)) >= 2,
            name=f"min_contributors_{j}",
        )

    # Linking + minimum delivery: if y=0 then x=0; if y=1 then x >= min_delivery[i]
    for i in range(n_producers):
        for j in range(n_contracts):
            model.addConstr(
                x[i, j] >= min_delivery[i] * y[i, j],
                name=f"min_delivery_{i}_{j}",
            )
            # Big-M upper bound: x[i, j] cannot exceed capacity[i]
            model.addConstr(
                x[i, j] <= capacity[i] * y[i, j],
                name=f"link_{i}_{j}",
            )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"status_{model.status}"}