import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    shipping_cost_f0 = params["shipping_cost_f0"]
    shipping_cost_f1 = params["shipping_cost_f1"]
    shipping_cost_f2 = params["shipping_cost_f2"]
    shipping_cost_f3 = params["shipping_cost_f3"]
    capacity = params["capacity"]

    num_facilities = 4
    num_customers = 8

    shipping_cost = [
        shipping_cost_f0,
        shipping_cost_f1,
        shipping_cost_f2,
        shipping_cost_f3,
    ]

    facilities = range(num_facilities)
    customers = range(num_customers)

    model = gp.Model("facility_location")
    model.setParam("OutputFlag", 0)

    # Binary open/close decision for each facility
    open_facility = model.addVars(facilities, vtype=GRB.BINARY, name="open")

    # Continuous shipment from facility f to customer c
    ship = model.addVars(facilities, customers, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    # Objective: minimize fixed costs + shipping costs
    model.setObjective(
        gp.quicksum(fixed_cost[f] * open_facility[f] for f in facilities)
        + gp.quicksum(shipping_cost[f][c] * ship[f, c] for f in facilities for c in customers),
        GRB.MINIMIZE,
    )

    # Demand fulfillment: each customer's demand must be exactly met
    for c in customers:
        model.addConstr(
            gp.quicksum(ship[f, c] for f in facilities) == demand[c],
            name=f"demand_{c}",
        )

    # Capacity limits: total shipment from a facility cannot exceed its capacity
    for f in facilities:
        model.addConstr(
            gp.quicksum(ship[f, c] for c in customers) <= capacity[f] * open_facility[f],
            name=f"capacity_{f}",
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