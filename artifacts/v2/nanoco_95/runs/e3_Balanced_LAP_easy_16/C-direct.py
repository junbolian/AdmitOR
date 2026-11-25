import gurobipy as gp
from gurobipy import GRB

def solve(params):
    costs = params["costs"]
    n_drivers = len(costs)
    n_routes = len(costs[0])

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_drivers, n_routes, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(costs[i][j] * x[i, j] for i in range(n_drivers) for j in range(n_routes)),
        GRB.MINIMIZE
    )

    for i in range(n_drivers):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n_routes)) == 1, name=f"driver_{i}")

    for j in range(n_routes):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n_drivers)) == 1, name=f"route_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}