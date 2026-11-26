import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supplies = params["supplies"]
    demands = params["demands"]
    transport_costs = params["transport_costs"]

    n = len(supplies)

    # transport_costs is row-major for i<j pairs (n*(n-1)/2 entries)
    # but costs are directed/asymmetric per problem description.
    # We build a symmetric cost matrix from the i<j entries.
    cost = {}
    idx = 0
    for i in range(n):
        for j in range(i + 1, n):
            c = transport_costs[idx]
            cost[i, j] = c
            cost[j, i] = c
            idx += 1

    model = gp.Model("warehouse_rebalancing")
    model.setParam("OutputFlag", 0)

    x = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                x[i, j] = model.addVar(lb=0.0, name=f"x_{i}_{j}")

    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in range(n) for j in range(n) if i != j),
        GRB.MINIMIZE
    )

    for i in range(n):
        inflow = gp.quicksum(x[j, i] for j in range(n) if j != i)
        outflow = gp.quicksum(x[i, j] for j in range(n) if j != i)
        model.addConstr(supplies[i] + inflow - outflow >= demands[i], name=f"balance_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}