import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_nodes = params["num_nodes"]
    source = params["source"]
    sink = params["sink"]
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]

    arcs = [[0,1],[1,2],[1,4],[1,5],[1,7],[2,3],[3,4],[4,5],[4,8],[4,9],[5,6],[5,7],[6,7],[7,8],[8,9]]

    model = gp.Model("min_cut")
    model.setParam("OutputFlag", 0)

    # x[i] = 1 if node i is in source set S, 0 if in sink set T
    x = model.addVars(num_nodes, vtype=GRB.BINARY, name="x")

    # y[k] = 1 if arc k crosses from S to T (i.e., tail in S, head in T)
    y = model.addVars(len(arcs), vtype=GRB.BINARY, name="y")

    # Source must be in S, sink must be in T
    model.addConstr(x[source] == 1, name="source_in_S")
    model.addConstr(x[sink] == 0, name="sink_in_T")

    # y[k] >= x[tail] - x[head] for each arc k = (tail, head)
    # This forces y[k] = 1 whenever tail is in S (x=1) and head is in T (x=0)
    for k, (tail, head) in enumerate(arcs):
        model.addConstr(y[k] >= x[tail] - x[head], name=f"cut_arc_{k}")

    # Minimize total cut cost
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