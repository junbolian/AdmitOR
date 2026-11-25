import gurobipy as gp
from gurobipy import GRB

def solve(params):
    hubs = [0, 1, 2]
    areas = [3, 4, 5, 6]

    supply = {
        0: params["supply_hub0"],
        1: params["supply_hub1"],
        2: params["supply_hub2"],
    }

    demand = {
        3: params["demand_area3"],
        4: params["demand_area4"],
        5: params["demand_area5"],
        6: params["demand_area6"],
    }

    capacity = {
        (i, j): params[f"capacity_arc_{i}_{j}"]
        for i in hubs for j in areas
    }

    cost = {
        (i, j): params[f"cost_arc_{i}_{j}"]
        for i in hubs for j in areas
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = {
        (i, j): model.addVar(lb=0.0, ub=capacity[(i, j)], name=f"x_{i}_{j}")
        for i in hubs for j in areas
    }

    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[(i, j)] for i in hubs for j in areas),
        GRB.MINIMIZE
    )

    for i in hubs:
        model.addConstr(
            gp.quicksum(x[(i, j)] for j in areas) == supply[i],
            name=f"supply_{i}"
        )

    for j in areas:
        model.addConstr(
            gp.quicksum(x[(i, j)] for i in hubs) == demand[j],
            name=f"demand_{j}"
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