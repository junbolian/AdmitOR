import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    shipping_cost = params["shipping_cost"]

    num_facilities = len(fixed_cost)
    num_customers = len(demand)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    open_facility = model.addVars(num_facilities, vtype=GRB.BINARY, name="open")
    ship = model.addVars(num_facilities, num_customers, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    # Objective: minimize fixed costs + shipping costs
    model.setObjective(
        gp.quicksum(fixed_cost[i] * open_facility[i] for i in range(num_facilities)) +
        gp.quicksum(shipping_cost[i][j] * ship[i, j] for i in range(num_facilities) for j in range(num_customers)),
        GRB.MINIMIZE
    )

    # Demand constraints: each customer's demand must be fully met
    for j in range(num_customers):
        model.addConstr(
            gp.quicksum(ship[i, j] for i in range(num_facilities)) == demand[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: total shipped from facility cannot exceed capacity if open
    for i in range(num_facilities):
        model.addConstr(
            gp.quicksum(ship[i, j] for j in range(num_customers)) <= capacity[i] * open_facility[i],
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