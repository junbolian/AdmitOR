import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 7
    cities = range(n)
    dist = {}
    for i in cities:
        for j in cities:
            dist[i, j] = 0.0 if i == j else float(params[f"distance_{i}_{j}"])

    pos_min = float(params["position_min"])
    pos_max = float(params["position_max"])

    model = gp.Model("delivery_tsp")
    model.Params.OutputFlag = 0

    x = model.addVars(n, n, vtype=GRB.BINARY, name="x")
    p = model.addVars(n, lb=pos_min, ub=pos_max, vtype=GRB.INTEGER, name="p")

    model.addConstrs((x[i, i] == 0 for i in cities), name="no_self_loop")
    model.addConstrs((gp.quicksum(x[i, j] for j in cities) == 1 for i in cities), name="leave_once")
    model.addConstrs((gp.quicksum(x[i, j] for i in cities) == 1 for j in cities), name="enter_once")

    model.addConstr(p[0] == pos_min, name="start_position")
    model.addConstrs((p[i] >= pos_min + 1 for i in range(1, n)), name="after_start_min")

    model.addConstrs(
        (
            p[i] - p[j] + n * x[i, j] <= n - 1
            for i in range(1, n)
            for j in range(1, n)
            if i != j
        ),
        name="mtz",
    )

    model.setObjective(gp.quicksum(dist[i, j] * x[i, j] for i in cities for j in cities), GRB.MINIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    return {"objective": None, "status": f"gurobi_status_{model.Status}"}