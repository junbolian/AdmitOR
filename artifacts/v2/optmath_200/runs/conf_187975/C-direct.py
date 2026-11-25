import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n_facilities = 7
    n_centers = 6

    supply = [params[f"supply_{i}"] for i in range(n_facilities)]
    demand = [params[f"demand_{j}"] for j in range(n_centers)]
    cost = [params[f"cost_{i}"] for i in range(n_facilities)]
    cap = [params[f"cap_{i}"] for i in range(n_facilities)]

    model = gp.Model("transportation")
    model.setParam("OutputFlag", 0)

    x = {}
    for i in range(n_facilities):
        for j in range(n_centers):
            x[i, j] = model.addVar(lb=0.0, ub=cap[i][j], name=f"x_{i}_{j}")

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(n_facilities) for j in range(n_centers)),
        GRB.MINIMIZE
    )

    for i in range(n_facilities):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_centers)) <= supply[i],
            name=f"supply_{i}"
        )

    for j in range(n_centers):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_facilities)) >= demand[j],
            name=f"demand_{j}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}