import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = params["capacity"]          # list of length 4
    contract_demand = params["contract_demand"]  # list of length 5
    min_delivery = params["min_delivery"]  # list of length 4
    cost = params["cost"]                  # 4x5 matrix

    num_producers = 4
    num_contracts = 5

    producers = range(num_producers)
    contracts = range(num_contracts)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j]: amount producer i delivers to contract j
    x = model.addVars(producers, contracts, lb=0.0, name="x")

    # y[i,j]: binary, 1 if producer i contributes to contract j
    y = model.addVars(producers, contracts, vtype=GRB.BINARY, name="y")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in producers for j in contracts),
        GRB.MINIMIZE
    )

    # Capacity constraints: each producer cannot exceed their capacity
    for i in producers:
        model.addConstr(
            gp.quicksum(x[i, j] for j in contracts) <= capacity[i],
            name=f"cap_{i}"
        )

    # Demand constraints: each contract must receive at least its required amount
    for j in contracts:
        model.addConstr(
            gp.quicksum(x[i, j] for i in producers) >= contract_demand[j],
            name=f"demand_{j}"
        )

    # At least two producers must contribute to each contract
    for j in contracts:
        model.addConstr(
            gp.quicksum(y[i, j] for i in producers) >= 2,
            name=f"min_producers_{j}"
        )

    # Linking constraints: if producer i contributes to contract j, x[i,j] >= min_delivery[i]
    # Use big-M: x[i,j] >= min_delivery[i] * y[i,j]
    # Also: x[i,j] <= capacity[i] * y[i,j]  (force y=0 when x=0)
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