import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    min_contributors = params["min_contributors"]
    min_delivery = params["min_delivery"]
    n_producers = params["n_producers"]
    n_contracts = params["n_contracts"]

    producers = range(n_producers)
    contracts = range(n_contracts)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j] = electricity delivered from producer i to contract j
    x = model.addVars(producers, contracts, lb=0.0, name="x")

    # y[i,j] = 1 if producer i contributes to contract j
    y = model.addVars(producers, contracts, vtype=GRB.BINARY, name="y")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in producers for j in contracts),
        GRB.MINIMIZE
    )

    # Capacity constraints: total delivery from producer i across all contracts <= capacity[i]
    for i in producers:
        model.addConstr(
            gp.quicksum(x[i, j] for j in contracts) <= capacity[i],
            name=f"cap_{i}"
        )

    # Demand constraints: total delivery to contract j >= demand[j]
    for j in contracts:
        model.addConstr(
            gp.quicksum(x[i, j] for i in producers) >= demand[j],
            name=f"demand_{j}"
        )

    # Minimum contributors: sum of y[i,j] over producers >= min_contributors[j]
    for j in contracts:
        model.addConstr(
            gp.quicksum(y[i, j] for i in producers) >= min_contributors[j],
            name=f"min_contrib_{j}"
        )

    # Linking constraints: if y[i,j]=1, x[i,j] >= min_delivery[i]; if y[i,j]=0, x[i,j]=0
    # Use big-M: x[i,j] <= capacity[i] * y[i,j]  (upper bound when y=0 forces x=0)
    #            x[i,j] >= min_delivery[i] * y[i,j] (lower bound when y=1 enforces min delivery)
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