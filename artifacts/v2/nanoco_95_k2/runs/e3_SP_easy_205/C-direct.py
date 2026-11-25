import gurobipy as gp
from gurobipy import GRB

def solve(params):
    arc_costs = params["arc_costs"]
    arc_capacities = params["arc_capacities"]
    node_supply = params["node_supply"]

    arcs = [
        (0, 1), (0, 2), (0, 6), (0, 8),
        (1, 2), (1, 5),
        (2, 3), (2, 6),
        (3, 4), (3, 7),
        (4, 5),
        (5, 6), (5, 7),
        (6, 7), (6, 8),
        (7, 8)
    ]

    num_nodes = 9

    model = gp.Model("amr_shortest_path")
    model.setParam("OutputFlag", 0)

    flow = {}
    for idx, arc in enumerate(arcs):
        flow[arc] = model.addVar(
            lb=0.0,
            ub=arc_capacities[idx],
            obj=arc_costs[idx],
            vtype=GRB.CONTINUOUS,
            name=f"flow_{arc[0]}_{arc[1]}"
        )

    model.ModelSense = GRB.MINIMIZE

    for node in range(num_nodes):
        outflow = gp.quicksum(flow[arc] for arc in arcs if arc[0] == node)
        inflow = gp.quicksum(flow[arc] for arc in arcs if arc[1] == node)
        model.addConstr(outflow - inflow == node_supply[node], name=f"balance_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}