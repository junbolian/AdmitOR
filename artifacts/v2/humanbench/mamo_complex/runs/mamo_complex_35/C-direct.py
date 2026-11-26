import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]

    costs = {
        (1, 2): params["cost_1_to_2"],
        (1, 3): params["cost_1_to_3"],
        (1, 4): params["cost_1_to_4"],
        (2, 1): params["cost_2_to_1"],
        (2, 3): params["cost_2_to_3"],
        (2, 4): params["cost_2_to_4"],
        (3, 1): params["cost_3_to_1"],
        (3, 2): params["cost_3_to_2"],
        (3, 4): params["cost_3_to_4"],
        (4, 1): params["cost_4_to_1"],
        (4, 2): params["cost_4_to_2"],
        (4, 3): params["cost_4_to_3"],
    }

    cities = [1, 2, 3, 4]
    arcs = list(costs.keys())

    model = gp.Model("vaccine_distribution")
    model.setParam("OutputFlag", 0)

    # Decision variables: flow from city i to city j
    x = model.addVars(arcs, lb=0.0, name="x")

    # Objective: minimize total transport cost
    model.setObjective(
        gp.quicksum(costs[i, j] * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    # Flow balance constraints: supply[i] + inflow[i] - outflow[i] >= demand[i]
    # Equivalently: net outflow <= supply[i] - demand[i]
    for city in cities:
        inflow = gp.quicksum(x[i, j] for (i, j) in arcs if j == city)
        outflow = gp.quicksum(x[i, j] for (i, j) in arcs if i == city)
        # supply[city-1] + inflow - outflow >= demand[city-1]
        model.addConstr(
            supply[city - 1] + inflow - outflow >= demand[city - 1],
            name=f"balance_{city}"
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