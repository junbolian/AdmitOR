import gurobipy as gp
from gurobipy import GRB


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    capacity_0 = params["capacity_0"]
    capacity_1 = params["capacity_1"]
    capacity_2 = params["capacity_2"]
    cost_0 = params["cost_0"]
    cost_1 = params["cost_1"]
    cost_2 = params["cost_2"]

    hubs = [0, 1, 2]
    areas = [0, 1, 2, 3]  # indices into the per-hub lists (corresponding to areas 3,4,5,6)

    capacities = [capacity_0, capacity_1, capacity_2]
    costs = [cost_0, cost_1, cost_2]

    model = gp.Model("disaster_relief")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[h][a] = flow from hub h to area (3+a)
    x = [[model.addVar(lb=0.0, name=f"x_{h}_{a}") for a in areas] for h in hubs]

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(costs[h][a] * x[h][a] for h in hubs for a in areas),
        GRB.MINIMIZE
    )

    # Supply constraints: all stock at each hub must be fully dispatched
    for h in hubs:
        model.addConstr(
            gp.quicksum(x[h][a] for a in areas) == supply[h],
            name=f"supply_{h}"
        )

    # Demand constraints: each area's requirement must be precisely met
    for a in areas:
        model.addConstr(
            gp.quicksum(x[h][a] for h in hubs) == demand[a],
            name=f"demand_{a}"
        )

    # Capacity constraints on each arc
    for h in hubs:
        for a in areas:
            model.addConstr(
                x[h][a] <= capacities[h][a],
                name=f"cap_{h}_{a}"
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