import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    capacity = params["capacity"]
    shipping_cost = params["shipping_cost"]

    facilities = list(range(len(fixed_cost)))
    customers = list(range(len(demand)))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    open_fac = model.addVars(facilities, vtype=GRB.BINARY, name="open")
    ship = model.addVars(facilities, customers, lb=0.0, name="ship")

    model.setObjective(
        gp.quicksum(fixed_cost[i] * open_fac[i] for i in facilities) +
        gp.quicksum(shipping_cost[i][j] * ship[i, j] for i in facilities for j in customers),
        GRB.MINIMIZE
    )

    for j in customers:
        model.addConstr(
            gp.quicksum(ship[i, j] for i in facilities) == demand[j],
            name=f"demand_{j}"
        )

    for i in facilities:
        model.addConstr(
            gp.quicksum(ship[i, j] for j in customers) <= capacity[i] * open_fac[i],
            name=f"capacity_{i}"
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