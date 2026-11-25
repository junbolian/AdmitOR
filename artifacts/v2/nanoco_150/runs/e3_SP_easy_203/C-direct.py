import gurobipy as gp
from gurobipy import GRB

def solve(params):
    arc_costs = params["arc_costs"]
    arc_capacities = params["arc_capacities"]
    source_supply = params["source_supply"]
    sink_supply = params["sink_supply"]

    arcs = [
        (0, 1), (0, 2), (0, 3), (0, 6), (0, 7),
        (1, 2), (1, 5), (1, 7),
        (2, 3), (2, 5), (2, 6),
        (3, 4), (3, 5),
        (4, 5), (4, 6), (4, 7),
        (5, 6), (5, 7),
        (6, 7),
    ]

    nodes = list(range(8))

    supply = {nd: 0.0 for nd in nodes}
    supply[0] = source_supply
    supply[7] = sink_supply

    model = gp.Model("min_cost_flow")
    model.setParam("OutputFlag", 0)

    flow = {}
    for idx, (i, j) in enumerate(arcs):
        flow[(i, j)] = model.addVar(
            lb=0.0,
            ub=arc_capacities[idx],
            obj=arc_costs[idx],
            vtype=GRB.CONTINUOUS,
            name=f"flow_{i}_{j}",
        )

    model.ModelSense = GRB.MINIMIZE

    for nd in nodes:
        outflow = gp.quicksum(flow[(i, j)] for (i, j) in arcs if i == nd)
        inflow  = gp.quicksum(flow[(i, j)] for (i, j) in arcs if j == nd)
        model.addConstr(outflow - inflow == supply[nd], name=f"flow_balance_{nd}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}