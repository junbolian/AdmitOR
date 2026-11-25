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

    # Fixed topology: 17 directed arcs
    arcs = [
        (0, 1), (0, 2), (0, 3), (0, 7),
        (1, 2), (1, 5),
        (2, 3), (2, 5), (2, 6),
        (3, 4), (3, 5),
        (4, 5), (4, 6), (4, 7),
        (5, 6), (5, 7),
        (6, 7)
    ]

    assert len(arcs) == 17, "Arc list must have exactly 17 entries"
    assert len(arc_capacities) == 17
    assert len(arc_unit_costs) == 17

    cap = {arcs[i]: arc_capacities[i] for i in range(17)}

    model = gp.Model("min_cut")
    model.setParam("OutputFlag", 0)

    # x[v] = 1 if node v is in the source set S, 0 if in sink set T
    x = model.addVars(num_nodes, vtype=GRB.BINARY, name="x")

    # y[i,j] = 1 if arc (i,j) crosses the cut (i in S, j in T)
    y = model.addVars(arcs, vtype=GRB.BINARY, name="y")

    # Source must be in S, sink must be in T
    model.addConstr(x[source] == 1, name="source_in_S")
    model.addConstr(x[sink] == 0, name="sink_in_T")

    # y[i,j] >= x[i] - x[j]: arc crosses cut only if tail in S and head in T
    for (i, j) in arcs:
        model.addConstr(y[i, j] >= x[i] - x[j], name=f"cut_{i}_{j}")

    # Minimize total capacity of cut arcs
    model.setObjective(
        gp.quicksum(cap[i, j] * y[i, j] for (i, j) in arcs),
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
        return {"objective": None, "status": f"solver_status_{model.Status}"}