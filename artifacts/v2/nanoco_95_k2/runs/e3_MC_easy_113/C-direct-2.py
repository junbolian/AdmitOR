import gurobipy as gp
from gurobipy import GRB

def solve(params):
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]
    num_nodes = params["num_nodes"]
    source = params["source"]
    sink = params["sink"]
    coords_x = params["coords_x"]
    coords_y = params["coords_y"]

    arcs = [
        (0, 1), (0, 2), (0, 3), (0, 7),
        (1, 2), (1, 5),
        (2, 3), (2, 5), (2, 6),
        (3, 4), (3, 5),
        (4, 5), (4, 6), (4, 7),
        (5, 6), (5, 7),
        (6, 7),
    ]

    model = gp.Model("min_cut")
    model.setParam("OutputFlag", 0)

    # x[i] = 1 if node i is in the source set S, 0 if in sink set T
    x = model.addVars(num_nodes, vtype=GRB.BINARY, name="x")

    # y[a] = 1 if arc a crosses the cut (tail in S, head in T)
    y = model.addVars(len(arcs), vtype=GRB.BINARY, name="y")

    # source must be in S, sink must be in T
    model.addConstr(x[source] == 1, name="source_in_S")
    model.addConstr(x[sink] == 0, name="sink_in_T")

    # y[a] >= x[u] - x[v] for each arc (u, v): if u in S and v in T, arc crosses the cut
    for idx, (u, v) in enumerate(arcs):
        model.addConstr(y[idx] >= x[u] - x[v], name=f"cut_arc_{idx}")

    # Minimize total capacity of cut arcs
    model.setObjective(
        gp.quicksum(arc_capacities[idx] * y[idx] for idx in range(len(arcs))),
        GRB.MINIMIZE
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