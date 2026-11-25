import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = params["capacity"]        # list of length n_producers
    demand = params["demand"]            # list of length n_contracts
    min_producers = params["min_producers"]  # list of length n_contracts
    min_delivery = params["min_delivery"]    # list of length n_producers
    cost = params["cost"]                # 2D list [n_producers][n_contracts]

    n_producers = len(capacity)
    n_contracts = len(demand)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j]: electricity from producer i to contract j
    x = model.addVars(n_producers, n_contracts, lb=0.0, name="x")

    # y[i,j]: binary, 1 if producer i contributes to contract j
    y = model.addVars(n_producers, n_contracts, vtype=GRB.BINARY, name="y")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(n_producers) for j in range(n_contracts)),
        GRB.MINIMIZE
    )

    # Capacity constraints: each producer cannot exceed their capacity
    for i in range(n_producers):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_contracts)) <= capacity[i],
            name=f"cap_{i}"
        )

    # Demand constraints: each contract must receive at least the required amount
    for j in range(n_contracts):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_producers)) >= demand[j],
            name=f"demand_{j}"
        )

    # Minimum producers per contract
    for j in range(n_contracts):
        model.addConstr(
            gp.quicksum(y[i, j] for i in range(n_producers)) >= min_producers[j],
            name=f"min_prod_{j}"
        )

    # Linking x and y: if y[i,j]=0 then x[i,j]=0; if y[i,j]=1 then x[i,j] >= min_delivery[i]
    for i in range(n_producers):
        for j in range(n_contracts):
            # x[i,j] >= min_delivery[i] * y[i,j]
            model.addConstr(x[i, j] >= min_delivery[i] * y[i, j], name=f"min_del_{i}_{j}")
            # x[i,j] <= capacity[i] * y[i,j]
            model.addConstr(x[i, j] <= capacity[i] * y[i, j], name=f"link_up_{i}_{j}")

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