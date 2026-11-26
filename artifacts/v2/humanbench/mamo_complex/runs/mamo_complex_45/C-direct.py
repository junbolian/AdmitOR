import gurobipy as gp
from gurobipy import GRB


def solve(params):
    nodes = [1, 2, 3, 4, 5]

    # Undirected movement pairs; cost per car is the same either way
    edge_pairs = [(1, 3), (1, 4), (1, 5), (2, 3), (2, 4), (2, 5),
                  (3, 4), (3, 5), (4, 5)]

    def unit_cost(i, j):
        a, b = min(i, j), max(i, j)
        return params["cost_%d_%d" % (a, b)]

    supply = {i: params["supply_%d" % i] for i in nodes}
    demand = {i: params["demand_%d" % i] for i in nodes}

    model = gp.Model("railcar_relocation")
    model.Params.OutputFlag = 0

    # Flow variables for each directed traversal of each undirected pair
    flow = {}
    for (i, j) in edge_pairs:
        flow[(i, j)] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS,
                                     obj=unit_cost(i, j), name="f_%d_%d" % (i, j))
        flow[(j, i)] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS,
                                     obj=unit_cost(i, j), name="f_%d_%d" % (j, i))

    model.ModelSense = GRB.MINIMIZE

    # Net inflow at each node must cover its deficit (surplus cars may stay put)
    for n in nodes:
        inflow = 0.0
        outflow = 0.0
        for (i, j) in edge_pairs:
            if j == n:
                inflow += flow[(i, j)]
            if i == n:
                outflow += flow[(j, i)] if False else 0.0
        # recompute explicitly over directed flows
        inflow = gp.quicksum(flow[(i, j)] for (i, j) in edge_pairs if j == n) + \
                 gp.quicksum(flow[(j, i)] for (i, j) in edge_pairs if i == n and (j, i) in flow)
        # simpler: iterate all directed arcs
        inflow = gp.quicksum(v for (a, b), v in flow.items() if b == n)
        outflow = gp.quicksum(v for (a, b), v in flow.items() if a == n)
        model.addConstr(inflow - outflow >= demand[n] - supply[n],
                        name="balance_%d" % n)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": round(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "not_solved"}