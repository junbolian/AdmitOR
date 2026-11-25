import gurobipy as gp
from gurobipy import GRB

def solve(params):
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]
    # coords are non-optimization data, not used in model

    # Network topology: 17 arcs in order
    arcs = [
        (0, 1), (0, 2), (0, 3), (0, 7),
        (1, 2), (1, 5),
        (2, 3), (2, 5), (2, 6),
        (3, 4), (3, 5),
        (4, 5), (4, 6), (4, 7),
        (5, 6), (5, 7),
        (6, 7),
    ]

    num_nodes = 8
    source = 0
    sink = 7

    model = gp.Model("min_cut")
    model.setParam("OutputFlag", 0)

    # x[i] = 1 if node i is in the "contained zone" S (source side)
    x = model.addVars(num_nodes, vtype=GRB.BINARY, name="x")

    # y[k] = 1 if arc k is a cut arc (tail in S, head in T)
    y = model.addVars(len(arcs), vtype=GRB.BINARY, name="y")

    # source must be in S, sink must be in T
    model.addConstr(x[source] == 1, name="source_in_S")
    model.addConstr(x[sink] == 0, name="sink_in_T")

    # y[k] >= x[u] - x[v] for arc k = (u, v)
    # This forces y[k] = 1 whenever u is in S and v is in T
    for k, (u, v) in enumerate(arcs):
        model.addConstr(y[k] >= x[u] - x[v], name=f"cut_arc_{k}")

    # Minimize total capacity of cut arcs
    model.setObjective(
        gp.quicksum(arc_capacities[k] * y[k] for k in range(len(arcs))),
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