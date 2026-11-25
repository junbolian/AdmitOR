import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 7
    sp = params["supplier_pref_positions"]
    pp = params["plant_pref_positions"]

    model = gp.Model("stable_marriage")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(n):
        for j in range(n):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.update()

    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n)) == 1)
    for j in range(n):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n)) == 1)

    for i in range(n):
        for j in range(n):
            a_expr = gp.quicksum(
                x[i, k] for k in range(n)
                if sp[i][k] > sp[i][j]
            )
            b_expr = gp.quicksum(
                x[l, j] for l in range(n)
                if pp[j][l] > pp[j][i]
            )
            model.addConstr(a_expr + b_expr <= 1)

    model.setObjective(
        gp.quicksum(
            x[i, j] * (sp[i][j] + pp[j][i])
            for i in range(n) for j in range(n)
        ),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.status}"}