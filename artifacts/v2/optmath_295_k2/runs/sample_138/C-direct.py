import gurobipy as gp
from gurobipy import GRB


def solve(params):
    net_demand = params["net_demand"]  # list of 6 values
    cost = params["cost"]              # 6x5 list (skipped self-route)
    capacity = params["capacity"]      # 6x5 list (skipped self-route)

    n = 6

    # Build explicit (i, j) route index mapping from the 5-entry rows
    # For source i, the 5 destinations are all cities except i, in ascending order
    routes = []
    route_cost = {}
    route_cap = {}

    for i in range(n):
        dests = [j for j in range(n) if j != i]
        for idx, j in enumerate(dests):
            routes.append((i, j))
            route_cost[(i, j)] = cost[i][idx]
            route_cap[(i, j)] = capacity[i][idx]

    model = gp.Model("city_distribution")
    model.setParam("OutputFlag", 0)

    # Decision variables: flow on each route
    flow = model.addVars(routes, lb=0.0, name="flow")

    # Capacity constraints
    for (i, j) in routes:
        model.addConstr(flow[i, j] <= route_cap[(i, j)], name=f"cap_{i}_{j}")

    # Flow balance: outflow - inflow = -net_demand
    # net_demand > 0 means city needs more (demand), so inflow - outflow = net_demand
    # equivalently: outflow - inflow = -net_demand
    for i in range(n):
        outflow = gp.quicksum(flow[i, j] for j in range(n) if j != i)
        inflow = gp.quicksum(flow[j, i] for j in range(n) if j != i)
        model.addConstr(outflow - inflow == -net_demand[i], name=f"balance_{i}")

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(route_cost[(i, j)] * flow[i, j] for (i, j) in routes),
        GRB.MINIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}