import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    ship_cost = params["ship_cost"]
    capacity = params["capacity"]

    num_facilities = 4
    num_customers = 8
    facilities = range(num_facilities)
    customers = range(num_customers)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: open facility i
    open_facility = model.addVars(facilities, vtype=GRB.BINARY, name="open")

    # Continuous: units shipped from facility i to customer j
    ship = model.addVars(facilities, customers, lb=0.0, name="ship")

    # Objective: fixed costs + shipping costs
    model.setObjective(
        gp.quicksum(fixed_cost[i] * open_facility[i] for i in facilities) +
        gp.quicksum(ship_cost[i][j] * ship[i, j] for i in facilities for j in customers),
        GRB.MINIMIZE
    )

    # Demand fulfillment: each customer's demand must be exactly met
    for j in customers:
        model.addConstr(
            gp.quicksum(ship[i, j] for i in facilities) == demand[j],
            name=f"demand_{j}"
        )

    # Capacity limits: total shipped from facility i cannot exceed its capacity
    for i in facilities:
        model.addConstr(
            gp.quicksum(ship[i, j] for j in customers) <= capacity[i] * open_facility[i],
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