import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]
    n = len(cost)
    m = len(cost[0])

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = {(i, j): model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
         for i in range(n) for j in range(m)}

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(n) for j in range(m)),
        GRB.MINIMIZE
    )

    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(m)) == 1, name=f"agent_{i}")

    for j in range(m):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n)) == 1, name=f"ticket_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}