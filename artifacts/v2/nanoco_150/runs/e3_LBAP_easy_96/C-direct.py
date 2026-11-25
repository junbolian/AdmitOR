import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["cost_matrix"]
    n = 5

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if team i assigned to site j
    x = model.addVars(n, n, vtype=GRB.BINARY, name="x")
    # z = minimax variable
    z = model.addVar(lb=0.0, name="z")

    model.setObjective(z, GRB.MINIMIZE)

    # Each team assigned to exactly one site
    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n)) == 1, name=f"team_{i}")

    # Each site assigned to exactly one team
    for j in range(n):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n)) == 1, name=f"site_{j}")

    # z >= cost of each active assignment
    for i in range(n):
        for j in range(n):
            model.addConstr(z >= cost_matrix[i][j] * x[i, j], name=f"minimax_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}