import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]      # list of 5 values
    demand = params["demand"]              # list of 6 values
    capacity = params["capacity"]          # list of 5 values
    serving_cost = params["serving_cost"]  # 6x5 matrix (rows=customers, cols=facilities)

    n_facilities = 5
    n_customers = 6

    facilities = range(n_facilities)
    customers = range(n_customers)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: open facility j
    open_fac = model.addVars(facilities, vtype=GRB.BINARY, name="open")

    # Continuous variable: amount shipped from facility j to customer i
    ship = model.addVars(customers, facilities, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    # Objective: minimize fixed costs + variable serving costs
    model.setObjective(
        gp.quicksum(fixed_cost[j] * open_fac[j] for j in facilities) +
        gp.quicksum(serving_cost[i][j] * ship[i, j] for i in customers for j in facilities),
        GRB.MINIMIZE
    )

    # Demand satisfaction: each customer's demand must be fully met
    for i in customers:
        model.addConstr(
            gp.quicksum(ship[i, j] for j in facilities) == demand[i],
            name=f"demand_{i}"
        )

    # Capacity constraint: total shipped from facility j cannot exceed its capacity
    for j in facilities:
        model.addConstr(
            gp.quicksum(ship[i, j] for i in customers) <= capacity[j] * open_fac[j],
            name=f"capacity_{j}"
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