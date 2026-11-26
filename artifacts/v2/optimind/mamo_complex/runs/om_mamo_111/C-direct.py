import gurobipy as gp
from gurobipy import GRB


def solve(params):
    regions = [1, 2, 3, 4, 5]
    pairs = [(1, 2), (1, 3), (1, 4), (1, 5), (2, 3),
             (2, 4), (2, 5), (3, 4), (3, 5), (4, 5)]

    cost = {}
    for (i, j) in pairs:
        cost[(i, j)] = params["cost_%d%d" % (i, j)]

    supply = {r: params["supply_%d" % r] for r in regions}
    demand = {r: params["demand_%d" % r] for r in regions}

    model = gp.Model("railcar_relocation")
    model.Params.OutputFlag = 0

    # Allow flow in both directions for each pair
    x = {}
    for (i, j) in pairs:
        x[(i, j)] = model.addVar(lb=0, vtype=GRB.CONTINUOUS,
                                 name="x_%d_%d" % (i, j))
        x[(j, i)] = model.addVar(lb=0, vtype=GRB.CONTINUOUS,
                                 name="x_%d_%d" % (j, i))

    # Objective: minimize total transport cost (symmetric costs)
    obj = gp.quicksum(cost[(i, j)] * (x[(i, j)] + x[(j, i)]) for (i, j) in pairs)
    model.setObjective(obj, GRB.MINIMIZE)

    # Balance constraint: supply + inflow - outflow >= demand
    for r in regions:
        inflow = gp.quicksum(x[(other, r)]
                             for other in regions if other != r
                             and (min(r, other), max(r, other)) in pairs)
        outflow = gp.quicksum(x[(r, other)]
                              for other in regions if other != r
                              and (min(r, other), max(r, other)) in pairs)
        model.addConstr(supply[r] + inflow - outflow >= demand[r],
                        name="balance_%d" % r)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "not_optimal"}