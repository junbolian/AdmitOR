import gurobipy as gp
from gurobipy import GRB


def solve(params):
    wc = params["worker_costs"]

    def cost(w):
        if isinstance(wc, dict):
            return float(wc[w])
        return float(wc[w - 1])

    workers = range(1, 11)

    task_workers = {
        1: [1, 2, 3, 4, 6, 9, 10],
        2: [5, 6, 8, 9, 10],
        3: [3, 4, 5, 10],
        4: [3, 5, 6],
        5: [3, 5, 7, 9, 10],
        6: [2, 4, 6, 10],
        7: [1, 3, 4, 5, 7, 8, 9],
        8: [2, 3, 4, 5, 7, 8],
        9: [1, 3, 5, 6, 7],
        10: [1, 4, 5, 6, 9, 10],
        11: [2, 4, 5, 7, 10],
        12: [4, 5, 8, 10],
        13: [2, 3, 7, 9],
        14: [2, 4, 5, 6, 8, 9],
        15: [3, 4, 5, 6, 7, 9],
        16: [3, 4, 6, 7, 9, 10],
        17: [1, 3, 4, 5, 7],
        18: [2, 4, 5, 6, 10],
        19: [1, 6, 7, 9],
        20: [3, 6, 7, 9, 10],
        21: [4, 5, 6],
        22: [1, 3, 4, 5, 8, 9],
    }

    model = gp.Model("worker_assignment")
    x = {w: model.addVar(vtype=GRB.BINARY, name=f"x_{w}") for w in workers}

    model.setObjective(
        gp.quicksum(cost(w) * x[w] for w in workers),
        GRB.MINIMIZE,
    )

    for t, ws in task_workers.items():
        model.addConstr(gp.quicksum(x[w] for w in ws) >= 1, name=f"task_{t}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    if model.status in (GRB.INFEASIBLE, GRB.INF_OR_UNBD):
        return {"objective": None, "status": "infeasible"}

    return {"objective": None, "status": f"gurobi_status_{model.status}"}