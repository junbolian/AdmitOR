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
    sources = [0, 1, 2]
    sinks = [3, 4, 5, 6]

    cap = {
        (i, j): params[f"cap_{i}_{j}"]
        for i in sources
        for j in sinks
    }
    cost = {
        (i, j): params[f"cost_{i}_{j}"]
        for i in sources
        for j in sinks
    }

    model = gp.Model("vaccine_distribution")
    model.setParam("OutputFlag", 0)

    x = model.addVars(sources, sinks, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in sources for j in sinks),
        GRB.MINIMIZE,
    )

    for i in sources:
        model.addConstr(
            gp.quicksum(x[i, j] for j in sinks) == supply[i],
            name=f"supply_{i}",
        )

    for j in sinks:
        model.addConstr(
            gp.quicksum(x[i, j] for i in sources) == demand[j],
            name=f"demand_{j}",
        )

    for i in sources:
        for j in sinks:
            model.addConstr(x[i, j] <= cap[i, j], name=f"cap_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}