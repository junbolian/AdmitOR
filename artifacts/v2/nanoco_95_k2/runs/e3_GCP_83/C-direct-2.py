import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n_vars = 10
    edges = [
        (5, 8), (4, 9), (3, 7), (0, 3), (1, 4),
        (2, 3), (6, 7), (4, 5), (3, 9), (5, 9), (6, 9),
    ]
    max_regs = n_vars

    model = gp.Model("register_allocation")
    model.Params.OutputFlag = 0

    x = {}
    for v in range(n_vars):
        for r in range(max_regs):
            x[v, r] = model.addVar(vtype=GRB.BINARY, name=f"x_{v}_{r}")

    y = {}
    for r in range(max_regs):
        y[r] = model.addVar(vtype=GRB.BINARY, name=f"y_{r}")

    model.update()

    for v in range(n_vars):
        model.addConstr(gp.quicksum(x[v, r] for r in range(max_regs)) == 1)

    for (u, w) in edges:
        for r in range(max_regs):
            model.addConstr(x[u, r] + x[w, r] <= 1)

    for v in range(n_vars):
        for r in range(max_regs):
            model.addConstr(x[v, r] <= y[r])

    model.setObjective(gp.quicksum(y[r] for r in range(max_regs)), GRB.MINIMIZE)

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}