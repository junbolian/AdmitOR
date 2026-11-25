import gurobipy as gp
from gurobipy import GRB


def solve(params):
    supplies = params["supplies"]
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]

    arcs = [
        (0, 2), (0, 3), (1, 2), (1, 3),
        (2, 4), (2, 5), (3, 4), (3, 5),
        (0, 4), (0, 5), (1, 4), (1, 5),
    ]

    nodes = list(range(6))

    model = gp.Model("food_redistribution")
    model.setParam("OutputFlag", 0)

    flow = {}
    for idx, (i, j) in enumerate(arcs):
        flow[(i, j)] = model.addVar(
            lb=0.0,
            ub=arc_capacities[idx],
            obj=arc_unit_costs[idx],
            vtype=GRB.CONTINUOUS,
            name=f"flow_{i}_{j}",
        )

    model.ModelSense = GRB.MINIMIZE

    for node in nodes:
        outflow = gp.quicksum(flow[(i, j)] for (i, j) in arcs if i == node)
        inflow = gp.quicksum(flow[(i, j)] for (i, j) in arcs if j == node)
        model.addConstr(outflow - inflow == supplies[node], name=f"balance_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}