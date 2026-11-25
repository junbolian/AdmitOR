import gurobipy as gp
from gurobipy import GRB


def solve(params):
    n = 5
    nodes = list(range(n))
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]

    dist = {
        (0, 1): params["distance_01"],
        (0, 2): params["distance_02"],
        (0, 3): params["distance_03"],
        (0, 4): params["distance_04"],
        (1, 2): params["distance_12"],
        (1, 3): params["distance_13"],
        (1, 4): params["distance_14"],
        (2, 3): params["distance_23"],
        (2, 4): params["distance_24"],
        (3, 4): params["distance_34"],
    }

    M = params["large_constant_M"]
    k = params["num_facilities_to_select"]

    model = gp.Model("facility_selection")
    model.setParam("OutputFlag", 0)

    x = model.addVars(nodes, vtype=GRB.BINARY, name="x")
    y = model.addVars(pairs, vtype=GRB.BINARY, name="y")
    D = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name="D")

    model.setObjective(D, GRB.MAXIMIZE)

    model.addConstr(gp.quicksum(x[i] for i in nodes) == k, name="select_count")

    for (i, j) in pairs:
        d = dist[(i, j)]
        model.addConstr(D + M * y[(i, j)] <= M + d, name=f"min_dist_{i}_{j}")
        model.addConstr(y[(i, j)] <= x[i], name=f"y_le_x_{i}_{j}_a")
        model.addConstr(y[(i, j)] <= x[j], name=f"y_le_x_{i}_{j}_b")
        model.addConstr(y[(i, j)] >= x[i] + x[j] - 1, name=f"y_ge_x_{i}_{j}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status in (GRB.INFEASIBLE, GRB.INF_OR_UNBD):
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}