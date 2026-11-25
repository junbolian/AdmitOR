import gurobipy as gp
from gurobipy import GRB


def solve(params):
    supply = {
        0: params["supply_0"],
        1: params["supply_1"],
        2: params["supply_2"],
    }
    demand = {
        3: params["demand_3"],
        4: params["demand_4"],
        5: params["demand_5"],
        6: params["demand_6"],
    }

    hubs = [0, 1, 2]
    clinics = [3, 4, 5, 6]

    cap = {
        (i, j): params[f"cap_{i}_{j}"]
        for i in hubs
        for j in clinics
    }
    cost = {
        (i, j): params[f"cost_{i}_{j}"]
        for i in hubs
        for j in clinics
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = {
        (i, j): model.addVar(lb=0.0, name=f"x_{i}_{j}")
        for i in hubs
        for j in clinics
    }

    # Objective: minimize total shipping cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in hubs for j in clinics),
        GRB.MINIMIZE,
    )

    # Supply constraints: all stock at each hub must be dispatched
    for i in hubs:
        model.addConstr(
            gp.quicksum(x[i, j] for j in clinics) == supply[i],
            name=f"supply_{i}",
        )

    # Demand constraints: exact demand at each clinic must be met
    for j in clinics:
        model.addConstr(
            gp.quicksum(x[i, j] for i in hubs) == demand[j],
            name=f"demand_{j}",
        )

    # Capacity constraints on each corridor
    for i in hubs:
        for j in clinics:
            model.addConstr(x[i, j] <= cap[i, j], name=f"cap_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}