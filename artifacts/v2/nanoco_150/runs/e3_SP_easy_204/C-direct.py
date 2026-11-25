import gurobipy as gp
from gurobipy import GRB

def solve(params):
    arc_costs = {
        (0, 1): params["arc_cost_0_1"],
        (1, 2): params["arc_cost_1_2"],
        (1, 4): params["arc_cost_1_4"],
        (1, 5): params["arc_cost_1_5"],
        (1, 6): params["arc_cost_1_6"],
        (1, 7): params["arc_cost_1_7"],
        (2, 3): params["arc_cost_2_3"],
        (3, 4): params["arc_cost_3_4"],
        (4, 5): params["arc_cost_4_5"],
        (4, 8): params["arc_cost_4_8"],
        (4, 9): params["arc_cost_4_9"],
        (5, 6): params["arc_cost_5_6"],
        (5, 7): params["arc_cost_5_7"],
        (6, 7): params["arc_cost_6_7"],
        (7, 8): params["arc_cost_7_8"],
        (7, 9): params["arc_cost_7_9"],
        (8, 9): params["arc_cost_8_9"],
    }
    arc_capacity = params["arc_capacity"]
    source_supply = params["source_supply"]
    sink_supply = params["sink_supply"]

    nodes = list(range(10))
    arcs = list(arc_costs.keys())

    supply = {node: 0.0 for node in nodes}
    supply[0] = source_supply
    supply[9] = sink_supply

    model = gp.Model("cold_chain")
    model.setParam("OutputFlag", 0)

    flow = model.addVars(arcs, lb=0.0, ub=arc_capacity, name="flow")

    model.setObjective(
        gp.quicksum(arc_costs[arc] * flow[arc] for arc in arcs),
        GRB.MINIMIZE
    )

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