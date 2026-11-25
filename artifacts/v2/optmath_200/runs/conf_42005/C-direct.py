import gurobipy as gp
from gurobipy import GRB

def solve(params):
    net_supply = params["net_supply"]
    cost = params["cost"]
    capacity = params["capacity"]
    num_cities = params["num_cities"]

    n = num_cities  # structural constant (index-set size)

    # Build arc lists: for each origin i, destinations are all j != i in order
    # cost and capacity are ordered by origin city 0..n-1, then destination (all n*(n-1) arcs)
    arcs = []
    for i in range(n):
        for j in range(n):
            if i != j:
                arcs.append((i, j))

    # Map arc to flat index
    arc_index = {(i, j): idx for idx, (i, j) in enumerate(arcs)}

    model = gp.Model("resource_distribution")
    model.setParam("OutputFlag", 0)

    # Decision variables: flow on each arc
    x = {}
    for idx, (i, j) in enumerate(arcs):
        x[(i, j)] = model.addVar(lb=0.0, ub=capacity[idx], name=f"x_{i}_{j}")

    model.update()

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(cost[arc_index[(i, j)]] * x[(i, j)] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    # Flow balance constraints: outflow - inflow = net_supply for each city
    for i in range(n):
        outflow = gp.quicksum(x[(i, j)] for j in range(n) if j != i)
        inflow = gp.quicksum(x[(j, i)] for j in range(n) if j != i)
        model.addConstr(outflow - inflow == net_supply[i], name=f"balance_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}