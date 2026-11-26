import gurobipy as gp
from gurobipy import GRB


def solve(params):
    num_cities = int(params["num_cities"])
    source = 0
    sink = num_cities - 1

    arcs = []
    for i in range(num_cities):
        for j in range(num_cities):
            if i == j:
                continue
            key = "cap_%d_%d" % (i, j)
            if key in params:
                arcs.append((i, j, float(params[key])))

    model = gp.Model("maxflow")
    model.Params.OutputFlag = 0

    flow = {}
    for (i, j, cap) in arcs:
        flow[i, j] = model.addVar(lb=0.0, ub=cap, vtype=GRB.CONTINUOUS, name="f_%d_%d" % (i, j))

    # Net outflow of the source equals total shipped (the objective)
    total = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="total")
    model.addConstr(
        gp.quicksum(flow[source, j] for (i, j, _c) in arcs if i == source)
        - gp.quicksum(flow[k, source] for (k, l, _c) in arcs if l == source)
        == total
    )
    # Net inflow of the sink equals total received
    model.addConstr(
        gp.quicksum(flow[k, sink] for (k, l, _c) in arcs if l == sink)
        - gp.quicksum(flow[sink, j] for (i, j, _c) in arcs if i == sink)
        == total
    )

    # Flow conservation at every intermediate city
    for n in range(num_cities):
        if n == source or n == sink:
            continue
        model.addConstr(
            gp.quicksum(flow[i, j] for (i, j, _c) in arcs if j == n)
            - gp.quicksum(flow[i, j] for (i, j, _c) in arcs if i == n)
            == 0
        )

    model.setObjective(total, GRB.MAXIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "no_solution"}