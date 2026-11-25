import gurobipy as gp
from gurobipy import GRB

def solve(params):
    arcs = [
        (0, 1), (0, 7),
        (1, 2), (1, 7),
        (2, 3), (2, 6),
        (3, 4), (3, 5), (3, 8), (3, 9),
        (4, 5), (4, 8),
        (5, 6),
        (6, 7),
        (7, 8), (7, 9),
        (8, 9),
    ]

    cost = {
        (0, 1): params["arc_cost_0_1"],
        (0, 7): params["arc_cost_0_7"],
        (1, 2): params["arc_cost_1_2"],
        (1, 7): params["arc_cost_1_7"],
        (2, 3): params["arc_cost_2_3"],
        (2, 6): params["arc_cost_2_6"],
        (3, 4): params["arc_cost_3_4"],
        (3, 5): params["arc_cost_3_5"],
        (3, 8): params["arc_cost_3_8"],
        (3, 9): params["arc_cost_3_9"],
        (4, 5): params["arc_cost_4_5"],
        (4, 8): params["arc_cost_4_8"],
        (5, 6): params["arc_cost_5_6"],
        (6, 7): params["arc_cost_6_7"],
        (7, 8): params["arc_cost_7_8"],
        (7, 9): params["arc_cost_7_9"],
        (8, 9): params["arc_cost_8_9"],
    }

    supply_source = params["supply_source"]
    demand_sink = params["demand_sink"]
    intermediate_supply = params["intermediate_supply"]

    nodes = list(range(10))

    supply = {}
    supply[0] = supply_source
    supply[9] = -demand_sink
    for node in range(1, 9):
        supply[node] = intermediate_supply

    model = gp.Model("last_mile_delivery")
    model.setParam("OutputFlag", 0)

    flow = {}
    for arc in arcs:
        flow[arc] = model.addVar(lb=0.0, ub=1.0, obj=cost[arc], vtype=GRB.CONTINUOUS,
                                  name=f"flow_{arc[0]}_{arc[1]}")

    model.ModelSense = GRB.MINIMIZE

    for node in nodes:
        outflow = gp.quicksum(flow[arc] for arc in arcs if arc[0] == node)
        inflow = gp.quicksum(flow[arc] for arc in arcs if arc[1] == node)
        model.addConstr(outflow - inflow == supply[node], name=f"balance_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}