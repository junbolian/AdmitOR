import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    arc_capacity = params["arc_capacity"]
    arc_cost = params["arc_cost"]

    # Arcs ordered: (0->3, 0->4, 0->5, 0->6, 1->3, 1->4, 1->5, 1->6, 2->3, 2->4, 2->5, 2->6)
    arcs = [
        (0, 3), (0, 4), (0, 5), (0, 6),
        (1, 3), (1, 4), (1, 5), (1, 6),
        (2, 3), (2, 4), (2, 5), (2, 6),
    ]

    supply_nodes = [0, 1, 2]
    demand_nodes = [3, 4, 5, 6]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: flow on each arc
    flow = {}
    for idx, (i, j) in enumerate(arcs):
        flow[(i, j)] = model.addVar(
            lb=0.0,
            ub=arc_capacity[idx],
            obj=arc_cost[idx],
            name=f"flow_{i}_{j}"
        )

    model.ModelSense = GRB.MINIMIZE

    # Supply constraints: all supply must be shipped out
    for s_idx, s in enumerate(supply_nodes):
        outflow = gp.quicksum(flow[(s, j)] for (i, j) in arcs if i == s)
        model.addConstr(outflow == supply[s_idx], name=f"supply_{s}")

    # Demand constraints: each clinic's demand must be exactly met
    for d_idx, d in enumerate(demand_nodes):
        inflow = gp.quicksum(flow[(i, d)] for (i, j) in arcs if j == d)
        model.addConstr(inflow == demand[d_idx], name=f"demand_{d}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}