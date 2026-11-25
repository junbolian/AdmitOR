import gurobipy as gp
from gurobipy import GRB


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n_warehouses = len(supply)
    n_stores = len(demand)

    model = gp.Model("transportation")
    model.Params.OutputFlag = 0

    x = model.addVars(n_warehouses, n_stores, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(
            cost[i][j] * x[i, j]
            for i in range(n_warehouses)
            for j in range(n_stores)
        ),
        GRB.MINIMIZE,
    )

    for i in range(n_warehouses):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_stores)) == supply[i],
            name=f"supply_{i}",
        )

    for j in range(n_stores):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_warehouses)) == demand[j],
            name=f"demand_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}