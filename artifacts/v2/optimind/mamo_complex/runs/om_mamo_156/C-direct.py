import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = {
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
        (1, 4): params["cost_1_4"],
        (1, 5): params["cost_1_5"],
        (2, 3): params["cost_2_3"],
        (2, 4): params["cost_2_4"],
        (2, 5): params["cost_2_5"],
        (3, 4): params["cost_3_4"],
        (3, 5): params["cost_3_5"],
        (4, 5): params["cost_4_5"],
    }

    supply = {
        1: params["supply_1"],
        2: params["supply_2"],
        3: params["supply_3"],
        4: params["supply_4"],
        5: params["supply_5"],
    }

    demand = {
        1: params["demand_1"],
        2: params["demand_2"],
        3: params["demand_3"],
        4: params["demand_4"],
        5: params["demand_5"],
    }

    # All directed arcs (both directions for each unordered pair)
    arcs = {}
    for (i, j), c in cost.items():
        arcs[(i, j)] = c
        arcs[(j, i)] = c  # symmetric cost

    locations = [1, 2, 3, 4, 5]

    model = gp.Model("freight_car_relocation")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,j] = number of cars moved from i to j
    x = {}
    for (i, j) in arcs:
        x[(i, j)] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(arcs[(i, j)] * x[(i, j)] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    # Flow balance constraints for each location:
    # supply[i] + inflow[i] - outflow[i] >= demand[i]
    for loc in locations:
        inflow = gp.quicksum(x[(i, j)] for (i, j) in arcs if j == loc)
        outflow = gp.quicksum(x[(i, j)] for (i, j) in arcs if i == loc)
        model.addConstr(
            supply[loc] + inflow - outflow >= demand[loc],
            name=f"balance_{loc}"
        )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{status}"}