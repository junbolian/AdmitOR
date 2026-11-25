import gurobipy as gp
from gurobipy import GRB


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    num_warehouses = len(supply)
    num_stores = len(demand)

    model = gp.Model("transportation")

    x = model.addVars(
        num_warehouses,
        num_stores,
        lb=0,
        vtype=GRB.CONTINUOUS,
        name="ship",
    )

    model.setObjective(
        gp.quicksum(
            cost[i][j] * x[i, j]
            for i in range(num_warehouses)
            for j in range(num_stores)
        ),
        GRB.MINIMIZE,
    )

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

    for i in range(num_warehouses):
        for j in range(num_stores):
            model.addConstr(x[i, j] <= capacity[i][j], name=f"cap_{i}_{j}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "infeasible_or_unbounded"}
    if model.status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}

    return {"objective": None, "status": f"gurobi_status_{model.status}"}