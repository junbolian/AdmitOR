import gurobipy as gp
from gurobipy import GRB


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_origins = len(supply)
    n_dests = len(demand)

    model = gp.Model("transportation")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(n_origins):
        for j in range(n_dests):
            x[i, j] = model.addVar(
                lb=0.0,
                ub=float(capacity[i][j]),
                obj=float(cost[i][j]),
                name=f"x_{i}_{j}",
            )

    model.ModelSense = GRB.MINIMIZE

    for i in range(n_origins):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_dests)) == float(supply[i]),
            name=f"supply_{i}",
        )

    for j in range(n_dests):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_origins)) == float(demand[j]),
            name=f"demand_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}