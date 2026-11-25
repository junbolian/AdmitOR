import gurobipy as gp
from gurobipy import GRB


def solve(params):
    n_communities = 28
    n_depots = 10

    R1 = params["R1"]
    R2 = params["R2"]
    demand = params["demand"]
    efficiency_gain = params["efficiency_gain"]
    est_raw = params["establishment_cost"]
    if hasattr(est_raw, "__iter__") and not isinstance(est_raw, (str, bytes)):
        establishment_cost = list(est_raw)
    else:
        establishment_cost = [est_raw] * n_depots

    dist = [
        [11, 16, 21, 49, 78, 100, 64, 38, 41, 64],
        [29, 33, 16, 52, 61, 95, 60, 67, 62, 54],
        [64, 43, 71, 40, 81, 79, 53, 22, 13, 63],
        [62, 37, 65, 23, 64, 63, 35, 34, 14, 45],
        [70, 52, 63, 29, 13, 45, 20, 77, 60, 8],
        [56, 53, 43, 55, 43, 84, 55, 87, 77, 45],
        [15, 35, 8, 64, 81, 112, 75, 63, 64, 72],
        [60, 35, 59, 5, 45, 51, 18, 47, 28, 27],
        [32, 17, 41, 42, 79, 92, 58, 18, 22, 62],
        [22, 22, 13, 45, 61, 91, 55, 56, 51, 51],
        [25, 10, 33, 40, 74, 91, 55, 26, 27, 58],
        [73, 61, 62, 48, 20, 62, 41, 91, 77, 29],
        [43, 22, 50, 34, 74, 82, 50, 16, 9, 56],
        [4, 26, 10, 58, 81, 108, 71, 51, 54, 69],
        [46, 26, 42, 17, 39, 63, 26, 53, 39, 24],
        [62, 62, 49, 65, 50, 91, 65, 96, 86, 54],
        [49, 48, 36, 54, 48, 87, 56, 82, 73, 47],
        [6, 20, 16, 53, 79, 104, 67, 43, 46, 66],
        [14, 32, 4, 60, 77, 108, 72, 61, 62, 68],
        [75, 51, 73, 18, 35, 34, 8, 64, 44, 19],
        [33, 25, 44, 51, 88, 102, 67, 16, 28, 72],
        [56, 34, 62, 33, 74, 76, 47, 21, 4, 56],
        [106, 83, 101, 50, 37, 5, 35, 96, 76, 37],
        [23, 9, 30, 40, 74, 92, 56, 28, 29, 58],
        [55, 37, 64, 44, 86, 88, 59, 10, 13, 67],
        [23, 34, 9, 57, 69, 102, 67, 66, 64, 62],
        [34, 29, 24, 40, 50, 82, 47, 63, 55, 42],
        [24, 7, 30, 38, 72, 90, 54, 29, 28, 56],
    ]

    model = gp.Model("depot_location")
    model.Params.OutputFlag = 0

    x = model.addVars(n_depots, vtype=GRB.BINARY, name="x")
    y = model.addVars(n_communities, vtype=GRB.BINARY, name="y")

    for i in range(n_communities):
        covering = [j for j in range(n_depots) if dist[i][j] <= R1]
        model.addConstr(gp.quicksum(x[j] for j in covering) >= 1, name=f"cover_{i}")

    for i in range(n_communities):
        eligible = [j for j in range(n_depots) if dist[i][j] <= R2]
        model.addConstr(y[i] <= gp.quicksum(x[j] for j in eligible), name=f"elig_{i}")

    obj = (
        gp.quicksum(establishment_cost[j] * x[j] for j in range(n_depots))
        - gp.quicksum(efficiency_gain[i] * y[i] for i in range(n_communities))
    )
    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status in (GRB.INFEASIBLE, GRB.INF_OR_UNBD):
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "failed"}