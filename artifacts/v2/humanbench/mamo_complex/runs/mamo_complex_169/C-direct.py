import gurobipy as gp
from gurobipy import GRB


def solve(params):
    cap_flat = params["capacity"]
    n = 6
    source, sink = 0, 5

    # Build a 2D capacity dict from the flat list of 30 ordered pairs (i,j), i != j
    cap = {}
    idx = 0
    for i in range(n):
        for j in range(n):
            if i != j:
                cap[i, j] = cap_flat[idx]
                idx += 1

    model = gp.Model("maxflow")
    model.Params.OutputFlag = 0

    flow = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                flow[i, j] = model.addVar(
                    lb=0, ub=cap[i, j], vtype=GRB.CONTINUOUS, name=f"flow_{i}_{j}"
                )

    # Flow conservation at intermediate nodes
    for k in range(n):
        if k in (source, sink):
            continue
        model.addConstr(
            gp.quicksum(flow[i, k] for i in range(n) if i != k)
            == gp.quicksum(flow[k, j] for j in range(n) if j != k)
        )

    total = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="total")
    model.addConstr(total == gp.quicksum(flow[source, j] for j in range(n) if j != source))
    model.addConstr(total == gp.quicksum(flow[i, sink] for i in range(n) if i != sink))

    model.setObjective(total, GRB.MAXIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": "no_optimal_solution"}