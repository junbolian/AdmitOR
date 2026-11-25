import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = params["capacity"]
    demand = params["demand"]
    min_contributors = params["min_contributors"]
    min_delivery = params["min_delivery"]
    cost = params["cost"]

    num_producers = len(capacity)
    num_contracts = len(demand)

    producers = range(num_producers)
    contracts = range(num_contracts)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j] = energy delivered by producer i to contract j
    x = model.addVars(producers, contracts, lb=0.0, name="x")

    # y[i,j] = 1 if producer i contributes to contract j
    y = model.addVars(producers, contracts, vtype=GRB.BINARY, name="y")

    # Objective: minimize total production cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in producers for j in contracts),
        GRB.MINIMIZE
    )

    # Capacity: each producer's total delivery cannot exceed its capacity
    for i in producers:
        model.addConstr(
            gp.quicksum(x[i, j] for j in contracts) <= capacity[i],
            name=f"cap_{i}"
        )

    # Demand: each contract must receive at least its required energy
    for j in contracts:
        model.addConstr(
            gp.quicksum(x[i, j] for i in producers) >= demand[j],
            name=f"demand_{j}"
        )

    # Minimum contributors: each contract must have at least min_contributors producers
    for j in contracts:
        model.addConstr(
            gp.quicksum(y[i, j] for i in producers) >= min_contributors,
            name=f"min_contrib_{j}"
        )

    # Linking: if producer i contributes to contract j, deliver at least min_delivery[i]
    # x[i,j] >= min_delivery[i] * y[i,j]
    # x[i,j] <= capacity[i] * y[i,j]  (y=0 forces x=0)
    for i in producers:
        for j in contracts:
            model.addConstr(
                x[i, j] >= min_delivery[i] * y[i, j],
                name=f"min_del_{i}_{j}"
            )
            model.addConstr(
                x[i, j] <= capacity[i] * y[i, j],
                name=f"link_ub_{i}_{j}"
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