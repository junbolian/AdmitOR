import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = params["capacity"]        # list of length n_producers
    demand = params["demand"]            # list of length n_contracts
    min_contributors = params["min_contributors"]  # scalar or list
    min_delivery = params["min_delivery"]          # list of length n_producers
    cost = params["cost"]                # 2D list [n_producers][n_contracts]

    n_producers = len(capacity)
    n_contracts = len(demand)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j] = energy producer i delivers to contract j
    x = model.addVars(n_producers, n_contracts, lb=0.0, name="x")

    # y[i,j] = 1 if producer i contributes to contract j
    y = model.addVars(n_producers, n_contracts, vtype=GRB.BINARY, name="y")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(n_producers) for j in range(n_contracts)),
        GRB.MINIMIZE
    )

    # Capacity constraints: total output of producer i across all contracts <= capacity[i]
    for i in range(n_producers):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_contracts)) <= capacity[i],
            name=f"cap_{i}"
        )

    # Demand constraints: total energy delivered to contract j >= demand[j]
    for j in range(n_contracts):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_producers)) >= demand[j],
            name=f"dem_{j}"
        )

    # Minimum contributors per contract
    # min_contributors may be a scalar or a list
    for j in range(n_contracts):
        mc = min_contributors[j] if hasattr(min_contributors, "__len__") else min_contributors
        model.addConstr(
            gp.quicksum(y[i, j] for i in range(n_producers)) >= mc,
            name=f"min_contrib_{j}"
        )

    # Linking: if y[i,j]=0 then x[i,j]=0; if y[i,j]=1 then x[i,j] >= min_delivery[i]
    for i in range(n_producers):
        for j in range(n_contracts):
            # x[i,j] <= capacity[i] * y[i,j]  (y=0 forces x=0)
            model.addConstr(
                x[i, j] <= capacity[i] * y[i, j],
                name=f"link_ub_{i}_{j}"
            )
            # x[i,j] >= min_delivery[i] * y[i,j]  (y=1 enforces minimum delivery)
            model.addConstr(
                x[i, j] >= min_delivery[i] * y[i, j],
                name=f"link_lb_{i}_{j}"
            )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}