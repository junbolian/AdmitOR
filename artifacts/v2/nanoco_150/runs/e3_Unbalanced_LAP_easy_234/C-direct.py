import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["assignment_cost"]
    n_dev = 6
    n_bug = 6

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_dev, n_bug, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(n_dev) for j in range(n_bug)),
        GRB.MINIMIZE
    )

    for i in range(n_dev):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n_bug)) == 1, name=f"dev_{i}")

    for j in range(n_bug):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n_dev)) == 1, name=f"bug_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}