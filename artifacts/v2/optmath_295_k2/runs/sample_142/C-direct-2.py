import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    capacity = params["capacity"]
    shipping_cost_f0 = params["shipping_cost_f0"]
    shipping_cost_f1 = params["shipping_cost_f1"]
    shipping_cost_f2 = params["shipping_cost_f2"]
    shipping_cost_f3 = params["shipping_cost_f3"]

    num_facilities = 4
    num_customers = len(demand)

    shipping_costs = [
        shipping_cost_f0,
        shipping_cost_f1,
        shipping_cost_f2,
        shipping_cost_f3,
    ]

    facilities = range(num_facilities)
    customers = range(num_customers)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    open_var = model.addVars(facilities, vtype=GRB.BINARY, name="open")
    ship = model.addVars(facilities, customers, lb=0.0, name="ship")

    obj = gp.quicksum(fixed_cost[i] * open_var[i] for i in facilities)
    obj += gp.quicksum(
        shipping_costs[i][j] * ship[i, j]
        for i in facilities
        for j in customers
    )
    model.setObjective(obj, GRB.MINIMIZE)

    for j in customers:
        model.addConstr(
            gp.quicksum(ship[i, j] for i in facilities) == demand[j],
            name=f"demand_{j}"
        )

    for i in facilities:
        model.addConstr(
            gp.quicksum(ship[i, j] for j in customers) <= capacity[i] * open_var[i],
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
        return {"objective": None, "status": f"solver_status_{model.Status}"}