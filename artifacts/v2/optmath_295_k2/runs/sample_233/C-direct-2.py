import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]           # cost[i][j] or cost[i,j]
    capacity = params["capacity"]   # capacity[i]
    demand = params["demand"]       # demand[j]
    min_producers = params["min_producers"]  # min_producers[j]
    min_delivery = params["min_delivery"]    # min_delivery[i]

    num_producers = 4
    num_contracts = 5
    producers = range(num_producers)
    contracts = range(num_contracts)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j]: amount producer i delivers to contract j
    x = model.addVars(producers, contracts, lb=0.0, name="x")
    # y[i,j]: binary, 1 if producer i is assigned to contract j
    y = model.addVars(producers, contracts, vtype=GRB.BINARY, name="y")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in producers for j in contracts),
        GRB.MINIMIZE
    )

    # Capacity constraints: sum of deliveries by producer i across all contracts <= capacity[i]
    for i in producers:
        model.addConstr(
            gp.quicksum(x[i, j] for j in contracts) <= capacity[i],
            name=f"cap_{i}"
        )

    # Demand constraints: sum of deliveries to contract j >= demand[j]
    for j in contracts:
        model.addConstr(
            gp.quicksum(x[i, j] for i in producers) >= demand[j],
            name=f"dem_{j}"
        )

    # Minimum producers per contract
    for j in contracts:
        model.addConstr(
            gp.quicksum(y[i, j] for i in producers) >= min_producers[j],
            name=f"minprod_{j}"
        )

    # Minimum delivery if assigned (linking x and y)
    for i in producers:
        for j in contracts:
            # x[i,j] >= min_delivery[i] * y[i,j]
            model.addConstr(
                x[i, j] >= min_delivery[i] * y[i, j],
                name=f"mindelivery_{i}_{j}"
            )
            # x[i,j] <= capacity[i] * y[i,j]  (if not assigned, x must be 0)
            model.addConstr(
                x[i, j] <= capacity[i] * y[i, j],
                name=f"bigM_{i}_{j}"
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