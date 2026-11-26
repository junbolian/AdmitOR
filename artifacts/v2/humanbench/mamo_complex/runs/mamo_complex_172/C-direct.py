import gurobipy as gp
from gurobipy import GRB


def solve(params):
    capacity = params["capacity"]
    n = 9
    source, sink = 0, 8

    model = gp.Model("max_flow")
    model.Params.OutputFlag = 0

    flow = {}
    for i in range(n):
        for j in range(n):
            if i != j and capacity[i][j] > 0:
                flow[i, j] = model.addVar(lb=0.0, ub=capacity[i][j], vtype=GRB.CONTINUOUS, name=f"flow_{i}_{j}")

    total = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="total")

    for k in range(n):
        if k == source or k == sink:
            continue
        inflow = gp.quicksum(flow[i, k] for (i, j) in flow if j == k)
        outflow = gp.quicksum(flow[k, j] for (i, j) in flow if i == k)
        model.addConstr(inflow - outflow == 0, name=f"balance_{k}")

    src_out = gp.quicksum(flow[source, j] for (i, j) in flow if i == source)
    model.addConstr(src_out == total, name="source_out")
    snk_in = gp.quicksum(flow[i, sink] for (i, j) in flow if j == sink)
    model.addConstr(snk_in == total, name="sink_in")

    model.setObjective(total, GRB.MAXIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.objVal, "status": "optimal"}
    return {"objective": None, "status": "no_solution"}