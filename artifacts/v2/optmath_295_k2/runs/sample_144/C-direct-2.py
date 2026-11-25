import gurobipy as gp
from gurobipy import GRB


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    n_wh = len(supply)      # 12 warehouses
    n_st = len(demand)       # 14 stores

    model = gp.Model("transport")
    model.setParam("OutputFlag", 0)

    # x[i, j] = units shipped from warehouse i to store j
    x = model.addVars(n_wh, n_st, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(
            transport_cost[i][j] * x[i, j]
            for i in range(n_wh)
            for j in range(n_st)
        ),
        GRB.MINIMIZE,
    )

    # Each warehouse must ship exactly its supply
    for i in range(n_wh):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_st)) == supply[i],
            name=f"supply_{i}",
        )

    # Each store must receive exactly its demand
    for j in range(n_st):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_wh)) == demand[j],
            name=f"demand_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}