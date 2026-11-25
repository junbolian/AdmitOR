import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_nodes = params["num_nodes"]
    source = params["source"]
    sink = params["sink"]
    arcs = params["arcs"]
    arc_unit_costs = params["arc_unit_costs"]
    # arc_capacities read from params (available for constraint use if needed)
    arc_capacities = params["arc_capacities"]

    model = gp.Model("min_cost_cut")
    model.setParam("OutputFlag", 0)

    # Binary variable x[i] = 1 if node i is in source set S, 0 if in sink set T
    x = model.addVars(num_nodes, vtype=GRB.BINARY, name="x")

    # Binary variable y[k] = 1 if arc k crosses from S to T (i.e., is in the cut)
    y = model.addVars(len(arcs), vtype=GRB.BINARY, name="y")

    # Source must be in S, sink must be in T
    model.addConstr(x[source] == 1, name="source_in_S")
    model.addConstr(x[sink] == 0, name="sink_in_T")

    # y[k] = 1 iff arc k goes from a node in S to a node in T
    # y[k] >= x[u] - x[v]  (forced to 1 when u in S and v in T)
    # y[k] <= x[u]          (can only be 1 if u in S)
    # y[k] <= 1 - x[v]      (can only be 1 if v in T)
    for k, (u, v) in enumerate(arcs):
        model.addConstr(y[k] >= x[u] - x[v], name=f"cut_lb_{k}")
        model.addConstr(y[k] <= x[u], name=f"cut_ub1_{k}")
        model.addConstr(y[k] <= 1 - x[v], name=f"cut_ub2_{k}")

    # Objective: minimize sum of arc_unit_costs for arcs in the cut
    model.setObjective(
        gp.quicksum(arc_unit_costs[k] * y[k] for k in range(len(arcs))),
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