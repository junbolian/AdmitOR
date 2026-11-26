import gurobipy as gp
from gurobipy import GRB


def solve(params):
    nodes = [0, 1, 2, 3, 4, 5]
    arcs = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                key = "capacity_%d_%d" % (i, j)
                if key in params:
                    cap = float(params[key])
                    if cap > 0:
                        arcs[(i, j)] = cap

    model = gp.Model("maxflow")
    model.Params.OutputFlag = 0

    flow = model.addVars(arcs.keys(), lb=0.0, name="flow")

    # Capacity constraints
    for (i, j), cap in arcs.items():
        model.addConstr(flow[i, j] <= cap)

    # Flow conservation at intermediate nodes
    for k in (1, 2, 3, 4):
        inflow = gp.quicksum(flow[i, k] for (i, j) in arcs if j == k)
        outflow = gp.quicksum(flow[k, j] for (i, j) in arcs if i == k)
        model.addConstr(inflow == outflow)

    # Optional: no flow into source or out of sink beyond conservation
    # (not needed for max flow LP; conservation at 0 and 5 replaced by net flow)
    total = gp.quicksum(flow[0, j] for (i, j) in arcs if i == 0) - gp.quicksum(
        flow[i, 0] for (i, j) in arcs if j == 0
    )
    model.setObjective(total, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "failed: status %d" % model.Status}