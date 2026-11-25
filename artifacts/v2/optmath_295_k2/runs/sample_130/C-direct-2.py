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

    # x[i,j]: energy from producer i to contract j
    x = model.addVars(producers, contracts, lb=0.0, name="x")

    # y[i,j]: binary, 1 if producer i contributes to contract j
    y = model.addVars(producers, contracts, vtype=GRB.BINARY, name="y")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in producers for j in contracts),
        GRB.MINIMIZE
    )

    # Capacity constraints
    for i in producers:
        model.addConstr(
            gp.quicksum(x[i, j] for j in contracts) <= capacity[i],
            name=f"cap_{i}"
        )

    # Demand constraints
    for j in contracts:
        model.addConstr(
            gp.quicksum(x[i, j] for i in producers) >= demand[j],
            name=f"demand_{j}"
        )

    # Minimum contributors per contract (at least 2 producers)
    for j in contracts:
        model.addConstr(
            gp.quicksum(y[i, j] for i in producers) >= 2,
            name=f"min_contrib_{j}"
        )

    # Linking constraints: x[i,j] >= min_delivery[i] * y[i,j]
    # and x[i,j] <= capacity[i] * y[i,j]
    for i in producers:
        for j in contracts:
            model.addConstr(
                x[i, j] >= min_delivery[i] * y[i, j],
                name=f"min_del_{i}_{j}"
            )
            model.addConstr(
                x[i, j] <= capacity[i] * y[i, j],
                name=f"ub_link_{i}_{j}"
            )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}