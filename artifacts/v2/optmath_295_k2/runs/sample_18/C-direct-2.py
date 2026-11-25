import gurobipy as gp
from gurobipy import GRB


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost_matrix = params["cost_matrix"]

    num_warehouses = len(supply)
    num_stores = len(demand)

    model = gp.Model("transportation")

    x = {}
    for i in range(num_warehouses):
        for j in range(num_stores):
            x[i, j] = model.addVar(
                lb=0.0,
                ub=GRB.INFINITY,
                obj=cost_matrix[i][j],
                name=f"x_{i}_{j}",
            )

    model.modelSense = GRB.MINIMIZE

    for i in range(num_warehouses):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_stores)) == supply[i],
            name=f"supply_{i}",
        )

    for j in range(num_stores):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_warehouses)) == demand[j],
            name=f"demand_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}