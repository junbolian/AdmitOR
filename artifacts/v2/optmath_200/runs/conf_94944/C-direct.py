import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]        # 5x2
    demand = params["demand"]        # 6x2
    cost = params["cost"]            # 2x5x6
    link_capacity = params["link_capacity"]  # 5x6

    W = 5  # warehouses
    S = 6  # stores
    P = 2  # products

    model = gp.Model("distribution")
    model.Params.OutputFlag = 0

    # Decision variables: x[w, s, p] = units of product p shipped from warehouse w to store s
    x = model.addVars(W, S, P, lb=0.0, name="x")

    # Objective: minimize total shipping cost
    model.setObjective(
        gp.quicksum(cost[p][w][s] * x[w, s, p]
                    for w in range(W) for s in range(S) for p in range(P)),
        GRB.MINIMIZE
    )

    # Supply constraints: total shipped from warehouse w for product p <= supply[w][p]
    for w in range(W):
        for p in range(P):
            model.addConstr(
                gp.quicksum(x[w, s, p] for s in range(S)) <= supply[w][p],
                name=f"supply_w{w}_p{p}"
            )

    # Demand constraints: total received at store s for product p >= demand[s][p]
    for s in range(S):
        for p in range(P):
            model.addConstr(
                gp.quicksum(x[w, s, p] for w in range(W)) >= demand[s][p],
                name=f"demand_s{s}_p{p}"
            )

    # Link capacity constraints: total units (both products) from warehouse w to store s <= link_capacity[w][s]
    for w in range(W):
        for s in range(S):
            model.addConstr(
                gp.quicksum(x[w, s, p] for p in range(P)) <= link_capacity[w][s],
                name=f"link_w{w}_s{s}"
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