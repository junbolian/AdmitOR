import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    if not isinstance(opening_cost, (list, tuple)):
        opening_cost = [opening_cost] * 4
    if not isinstance(capacity, (list, tuple)):
        capacity = [capacity] * 4

    n_dc = 4
    n_stores = 6

    model = gp.Model("globalsupply")
    model.Params.OutputFlag = 0

    open_dc = model.addVars(n_dc, vtype=GRB.BINARY, name="open")
    ship = model.addVars(n_dc, n_stores, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    model.setObjective(
        gp.quicksum(open_dc[i] * opening_cost[i] for i in range(n_dc))
        + gp.quicksum(
            ship[i, j] * transport_cost[i][j]
            for i in range(n_dc)
            for j in range(n_stores)
        ),
        GRB.MINIMIZE,
    )

    for j in range(n_stores):
        model.addConstr(
            gp.quicksum(ship[i, j] for i in range(n_dc)) == demand[j],
            name=f"demand_{j}",
        )

    for i in range(n_dc):
        model.addConstr(
            gp.quicksum(ship[i, j] for j in range(n_stores)) <= capacity[i] * open_dc[i],
            name=f"capacity_{i}",
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"status_{model.Status}"}