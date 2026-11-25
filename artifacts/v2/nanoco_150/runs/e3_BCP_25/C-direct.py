import gurobipy as gp
from gurobipy import GRB


def solve(params):
    edges = [
        (0, 1, params["edge_0_1_weight"]),
        (0, 2, params["edge_0_2_weight"]),
        (0, 4, params["edge_0_4_weight"]),
        (1, 2, params["edge_1_2_weight"]),
        (1, 6, params["edge_1_6_weight"]),
        (2, 3, params["edge_2_3_weight"]),
        (2, 6, params["edge_2_6_weight"]),
        (3, 5, params["edge_3_5_weight"]),
    ]
    zones = list(range(7))

    total_w = sum(w for _, _, w in edges)
    U = max(total_w, 1)

    model = gp.Model("hazard")
    model.Params.OutputFlag = 0

    x = model.addVars(zones, lb=0, ub=U, vtype=GRB.INTEGER, name="x")
    z = model.addVar(lb=0, ub=U, vtype=GRB.INTEGER, name="z")
    b = model.addVars(range(len(edges)), vtype=GRB.BINARY, name="b")

    for i in zones:
        model.addConstr(z >= x[i])

    for k, (u, v, d) in enumerate(edges):
        M = U + d
        model.addConstr(x[u] - x[v] >= d - M * (1 - b[k]))
        model.addConstr(x[v] - x[u] >= d - M * b[k])

    model.setObjective(z, GRB.MINIMIZE)
    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(z.X), "status": "optimal"}
    return {"objective": None, "status": f"gurobi_status_{model.status}"}