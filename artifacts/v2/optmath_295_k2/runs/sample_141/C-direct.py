import gurobipy as gp
from gurobipy import GRB

def solve(params):
    pair_weights = params["pair_weights"]
    facilities_to_select = params["facilities_to_select"]

    nodes = [0, 1, 2, 3]
    pairs = [(0,1),(0,2),(0,3),(1,0),(1,2),(1,3),(2,0),(2,1),(2,3),(3,0),(3,1),(3,2)]

    # pair_weights is a list indexed by position in the pairs list
    weight = {p: pair_weights[idx] for idx, p in enumerate(pairs)}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(nodes, vtype=GRB.BINARY, name="x")
    z = model.addVars(pairs, vtype=GRB.BINARY, name="z")

    model.setObjective(
        gp.quicksum(weight[p] * z[p] for p in pairs),
        GRB.MAXIMIZE
    )

    model.addConstr(gp.quicksum(x[i] for i in nodes) == facilities_to_select, name="facility_count")

    for (i, j) in pairs:
        model.addConstr(z[i, j] <= x[i], name=f"zpair_xi_{i}_{j}")
        model.addConstr(z[i, j] <= x[j], name=f"zpair_xj_{i}_{j}")
        model.addConstr(z[i, j] >= x[i] + x[j] - 1, name=f"zpair_both_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}