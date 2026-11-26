import gurobipy as gp
from gurobipy import GRB

def solve(params):
    nodes = range(7)

    # Only build arcs for which a capacity param exists
    arcs = []
    cap = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                key = "capacity_%d_%d" % (i, j)
                if key in params:
                    arcs.append((i, j))
                    cap[(i, j)] = params[key]

    model = gp.Model("powerflow")
    model.Params.OutputFlag = 0

    flow = model.addVars(arcs, lb=0.0, name="flow")

    # Capacity constraints
    for (i, j) in arcs:
        model.addConstr(flow[i, j] <= cap[(i, j)], name="cap_%d_%d" % (i, j))

    source = 0
    sink = 6

    # Flow conservation at intermediate nodes (not source or sink)
    for k in nodes:
        if k == source or k == sink:
            continue
        outflow = gp.quicksum(flow[k, j] for j in nodes if (k, j) in cap)
        inflow = gp.quicksum(flow[i, k] for i in nodes if (i, k) in cap)
        model.addConstr(outflow - inflow == 0, name="balance_%d" % k)

    # Objective: maximize net flow out of source
    net_source_out = (
        gp.quicksum(flow[source, j] for j in nodes if (source, j) in cap)
        - gp.quicksum(flow[i, source] for i in nodes if (i, source) in cap)
    )

    model.setObjective(net_source_out, GRB.MAXIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}