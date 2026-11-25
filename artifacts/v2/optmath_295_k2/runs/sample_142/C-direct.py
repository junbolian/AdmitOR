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

    model = gp.Model("facility_location")
    model.setParam("OutputFlag", 0)

    open_fac = model.addVars(facilities, vtype=GRB.BINARY, name="open")
    ship = model.addVars(facilities, customers, lb=0.0, name="ship")

    model.setObjective(
        gp.quicksum(fixed_cost[i] * open_fac[i] for i in facilities)
        + gp.quicksum(
            shipping_costs[i][j] * ship[i, j]
            for i in facilities
            for j in customers
        ),
        GRB.MINIMIZE,
    )

    for j in customers:
        model.addConstr(
            gp.quicksum(ship[i, j] for i in facilities) == demand[j],
            name=f"demand_{j}",
        )

    for i in facilities:
        model.addConstr(
            gp.quicksum(ship[i, j] for j in customers) <= capacity[i] * open_fac[i],
            name=f"capacity_{i}",
        )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}