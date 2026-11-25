import gurobipy as gp
from gurobipy import GRB

def solve(params):
    coordinates = params["coordinates"]
    arc_min_flow = params["arc_min_flow"]
    arc_max_flow = params["arc_max_flow"]
    arc_unit_cost = params["arc_unit_cost"]
    num_nodes = params["num_nodes"]
    num_arcs = params["num_arcs"]

    arcs = [
        (0, 1), (0, 2), (0, 3), (0, 5),
        (1, 0), (1, 2),
        (2, 0), (2, 1), (2, 3), (2, 4),
        (3, 2), (3, 4), (3, 5),
        (4, 0), (4, 3), (4, 5),
        (5, 0), (5, 4),
    ]

    assert len(arcs) == num_arcs

    model = gp.Model("amr_flow")
    model.setParam("OutputFlag", 0)

    flow = {}
    for i, (u, v) in enumerate(arcs):
        flow[i] = model.addVar(
            lb=arc_min_flow[i],
            ub=arc_max_flow[i],
            vtype=GRB.INTEGER,
            name=f"flow_{i}"
        )

    # Flow conservation: inflow == outflow at every node
    for node in range(num_nodes):
        inflow = gp.quicksum(flow[i] for i, (u, v) in enumerate(arcs) if v == node)
        outflow = gp.quicksum(flow[i] for i, (u, v) in enumerate(arcs) if u == node)
        model.addConstr(inflow == outflow, name=f"balance_{node}")

    obj = gp.quicksum(arc_unit_cost[i] * flow[i] for i in range(num_arcs))
    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}