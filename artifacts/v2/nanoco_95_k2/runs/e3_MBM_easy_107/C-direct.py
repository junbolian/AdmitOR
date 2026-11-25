import gurobipy as gp
from gurobipy import GRB


def solve(params):
    users = list(range(7))
    freqs = list(range(5))

    feasible = [
        (0, 0), (0, 2), (0, 3),
        (1, 4),
        (2, 0), (2, 1), (2, 2),
        (3, 0), (3, 2), (3, 4),
        (4, 0), (4, 2), (4, 3), (4, 4),
        (5, 0),
    ]

    model = gp.Model("freq_alloc")
    model.Params.OutputFlag = 0

    x = {}
    for (i, j) in feasible:
        x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.update()

    for i in users:
        model.addConstr(
            gp.quicksum(x[i, j] for (ii, j) in feasible if ii == i) <= 1,
            name=f"user_cap_{i}",
        )

    for j in freqs:
        model.addConstr(
            gp.quicksum(x[i, j] for (i, jj) in feasible if jj == j) <= 1,
            name=f"freq_cap_{j}",
        )

    model.setObjective(gp.quicksum(x[i, j] for (i, j) in feasible), GRB.MAXIMIZE)

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}