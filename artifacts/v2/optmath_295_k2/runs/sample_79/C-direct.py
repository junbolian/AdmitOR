import gurobipy as gp
from gurobipy import GRB


def solve(params):
    supplies = params["supplies"]
    demands = params["demands"]
    transport_costs = params["transport_costs"]
    capacities = params["capacities"]

    n_warehouses = len(supplies)
    n_stores = len(demands)

    model = gp.Model("transportation")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(n_warehouses):
        for j in range(n_stores):
            x[i, j] = model.addVar(
                lb=0,
                ub=capacities[i][j],
                obj=transport_costs[i][j],
                name=f"x_{i}_{j}",
            )

    for i in range(n_warehouses):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_stores)) == supplies[i],
            name=f"supply_{i}",
        )

    for j in range(n_stores):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_warehouses)) == demands[j],
            name=f"demand_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}