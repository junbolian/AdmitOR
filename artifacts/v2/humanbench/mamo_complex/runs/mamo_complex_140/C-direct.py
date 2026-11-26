import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params.get("cost_matrix") or params.get("Cost_matrix") or list(params.values())[0]
    n = len(cost_matrix)
    cities = list(range(n))

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    x = {}
    for i in cities:
        for j in cities:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    for i in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for j in cities if j != i) == 1,
            name=f"leave_{i}"
        )

    for j in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for i in cities if i != j) == 1,
            name=f"enter_{j}"
        )

    u = {}
    for i in cities:
        u[i] = model.addVar(lb=0, ub=n - 1, vtype=GRB.CONTINUOUS, name=f"u_{i}")

    for i in cities:
        for j in cities:
            if i != j and j != 0:
                model.addConstr(
                    u[i] - u[j] + n * x[i, j] <= n - 1,
                    name=f"mtz_{i}_{j}"
                )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}