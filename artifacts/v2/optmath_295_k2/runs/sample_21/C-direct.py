import gurobipy as gp
from gurobipy import GRB

def solve(params):
    pairwise_distances = params["pairwise_distances"]
    num_facilities_to_open = params["num_facilities_to_open"]

    n = 5

    pairs = []
    for i in range(n):
        for j in range(n):
            if i != j:
                pairs.append((i, j))

    dist = {}
    for k, (i, j) in enumerate(pairs):
        dist[(i, j)] = pairwise_distances[k]

    model = gp.Model("facility_dispersion")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(n):
        x[i] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}")

    y = {}
    for (i, j) in pairs:
        y[(i, j)] = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{j}")

    model.update()

    model.setObjective(
        gp.quicksum(dist[(i, j)] * y[(i, j)] for (i, j) in pairs),
        GRB.MAXIMIZE,
    )

    model.addConstr(
        gp.quicksum(x[i] for i in range(n)) == num_facilities_to_open,
        name="total_facilities",
    )

    for (i, j) in pairs:
        model.addConstr(y[(i, j)] <= x[i], name=f"link_upper1_{i}_{j}")
        model.addConstr(y[(i, j)] <= x[j], name=f"link_upper2_{i}_{j}")
        model.addConstr(y[(i, j)] >= x[i] + x[j] - 1, name=f"link_lower_{i}_{j}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.objVal), "status": "optimal"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}