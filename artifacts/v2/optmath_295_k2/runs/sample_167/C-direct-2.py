import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    min_contributors = params["min_contributors"]
    min_delivery = params["min_delivery"]

    num_producers = 6
    num_contracts = 6
    producers = range(num_producers)
    contracts = range(num_contracts)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j] = electricity delivered by producer i to contract j
    x = model.addVars(producers, contracts, lb=0.0, name="x")
    # y[i,j] = 1 if producer i contributes to contract j
    y = model.addVars(producers, contracts, vtype=GRB.BINARY, name="y")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in producers for j in contracts),
        GRB.MINIMIZE
    )

    # Capacity constraints: total generation by producer i <= capacity[i]
    for i in producers:
        model.addConstr(
            gp.quicksum(x[i, j] for j in contracts) <= capacity[i],
            name=f"cap_{i}"
        )

    # Demand constraints: total delivery to contract j >= demand[j]
    for j in contracts:
        model.addConstr(
            gp.quicksum(x[i, j] for i in producers) >= demand[j],
            name=f"dem_{j}"
        )

    # Minimum contributors per contract
    for j in contracts:
        model.addConstr(
            gp.quicksum(y[i, j] for i in producers) >= min_contributors[j],
            name=f"mincontrib_{j}"
        )

    # Linking constraints: x[i,j] >= min_delivery[i] * y[i,j]
    # and x[i,j] <= capacity[i] * y[i,j]
    for i in producers:
        for j in contracts:
            model.addConstr(
                x[i, j] >= min_delivery[i] * y[i, j],
                name=f"mindelivery_{i}_{j}"
            )
            model.addConstr(
                x[i, j] <= capacity[i] * y[i, j],
                name=f"link_ub_{i}_{j}"
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