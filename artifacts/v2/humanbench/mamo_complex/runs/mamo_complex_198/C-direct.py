import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_1_3 = params["cost_1_3"]
    cost_1_4 = params["cost_1_4"]
    cost_1_5 = params["cost_1_5"]
    cost_2_3 = params["cost_2_3"]
    cost_2_4 = params["cost_2_4"]
    cost_2_5 = params["cost_2_5"]
    cost_3_4 = params["cost_3_4"]
    cost_3_5 = params["cost_3_5"]
    cost_4_5 = params["cost_4_5"]

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

    # Allowed directed moves (source, dest) with their costs
    # Cars can only move in a defined set of routes; we allow both directions
    # but costs are given one-directionally. We model both directions.
    # From the problem: routes are (1->3), (1->4), (1->5), (2->3), (2->4),
    # (2->5), (3->4), (3->5), (4->5) and their reverses.
    arc_costs = {
        (1, 3): cost_1_3,
        (3, 1): cost_1_3,
        (1, 4): cost_1_4,
        (4, 1): cost_1_4,
        (1, 5): cost_1_5,
        (5, 1): cost_1_5,
        (2, 3): cost_2_3,
        (3, 2): cost_2_3,
        (2, 4): cost_2_4,
        (4, 2): cost_2_4,
        (2, 5): cost_2_5,
        (5, 2): cost_2_5,
        (3, 4): cost_3_4,
        (4, 3): cost_3_4,
        (3, 5): cost_3_5,
        (5, 3): cost_3_5,
        (4, 5): cost_4_5,
        (5, 4): cost_4_5,
    }

    arcs = list(arc_costs.keys())
    nodes = [1, 2, 3, 4, 5]

    model = gp.Model("railroad_relocation")
    model.setParam("OutputFlag", 0)

    # Decision variables: number of cars moved along each arc (non-negative)
    x = model.addVars(arcs, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(arc_costs[arc] * x[arc] for arc in arcs),
        GRB.MINIMIZE
    )

    # Flow balance constraints: for each node,
    # supply + inflow - outflow >= demand
    # i.e., net outflow <= surplus (supply - demand if positive)
    # Equivalently: supply[i] + sum(inflow) - sum(outflow) >= demand[i]
    for node in nodes:
        inflow = gp.quicksum(x[(i, j)] for (i, j) in arcs if j == node)
        outflow = gp.quicksum(x[(i, j)] for (i, j) in arcs if i == node)
        model.addConstr(
            supply[node] + inflow - outflow >= demand[node],
            name=f"balance_{node}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": round(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}