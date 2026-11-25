import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = params["capacity"]      # list of length 4
    demand = params["demand"]          # list of length 5
    min_delivery = params["min_delivery"]  # list of length 4
    cost = params["cost"]              # 4x5 matrix

    num_producers = 4
    num_contracts = 5
    producers = range(num_producers)
    contracts = range(num_contracts)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j]: energy delivered from producer i to contract j
    x = model.addVars(producers, contracts, lb=0.0, name="x")

    # y[i,j]: binary, 1 if producer i contributes to contract j
    y = model.addVars(producers, contracts, vtype=GRB.BINARY, name="y")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in producers for j in contracts),
        GRB.MINIMIZE
    )

    # Capacity constraints: total allocation per producer <= capacity
    for i in producers:
        model.addConstr(
            gp.quicksum(x[i, j] for j in contracts) <= capacity[i],
            name=f"cap_{i}"
        )

    # Demand constraints: total allocation per contract >= demand
    for j in contracts:
        model.addConstr(
            gp.quicksum(x[i, j] for i in producers) >= demand[j],
            name=f"demand_{j}"
        )

    # Minimum contributors: at least 2 producers per contract
    for j in contracts:
        model.addConstr(
            gp.quicksum(y[i, j] for i in producers) >= 2,
            name=f"min_contrib_{j}"
        )

    # Minimum delivery: if producer i contributes to contract j, deliver at least min_delivery[i]
    # x[i,j] >= min_delivery[i] * y[i,j]
    # x[i,j] <= capacity[i] * y[i,j]  (linking: if y=0 then x=0)
    for i in producers:
        for j in contracts:
            model.addConstr(
                x[i, j] >= min_delivery[i] * y[i, j],
                name=f"min_del_{i}_{j}"
            )
            model.addConstr(
                x[i, j] <= capacity[i] * y[i, j],
                name=f"link_{i}_{j}"
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