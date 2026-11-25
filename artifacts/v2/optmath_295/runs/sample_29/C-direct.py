import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    shipping_cost = params["shipping_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    num_facilities = 5
    num_customers = 7

    facilities = range(num_facilities)
    customers = range(num_customers)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    open_facility = model.addVars(facilities, vtype=GRB.BINARY, name="open")
    ship = model.addVars(facilities, customers, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    # Objective: minimize fixed costs + shipping costs
    model.setObjective(
        gp.quicksum(fixed_cost[i] * open_facility[i] for i in facilities) +
        gp.quicksum(shipping_cost[i][j] * ship[i, j] for i in facilities for j in customers),
        GRB.MINIMIZE
    )

    # Demand satisfaction: each customer's demand must be met exactly
    for j in customers:
        model.addConstr(
            gp.quicksum(ship[i, j] for i in facilities) == demand[j],
            name=f"demand_{j}"
        )

    # Capacity and activation: shipments from facility i cannot exceed capacity[i] * open_facility[i]
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
        return {"objective": None, "status": f"solver_status_{model.Status}"}