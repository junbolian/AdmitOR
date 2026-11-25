import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]   # list of length 4
    demand = params["demand"]           # list of length 10
    ship_cost = params["ship_cost"]     # 4x10 nested list
    capacity = params["capacity"]       # list of length 4

    num_facilities = 4
    num_customers = 10
    facilities = range(num_facilities)
    customers = range(num_customers)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: open facility i
    open_fac = model.addVars(facilities, vtype=GRB.BINARY, name="open")

    # Continuous: units shipped from facility i to customer j
    ship = model.addVars(facilities, customers, lb=0.0, name="ship")

    # Objective: fixed costs + shipping costs
    model.setObjective(
        gp.quicksum(fixed_cost[i] * open_fac[i] for i in facilities) +
        gp.quicksum(ship_cost[i][j] * ship[i, j] for i in facilities for j in customers),
        GRB.MINIMIZE
    )

    # Demand satisfaction: total shipped to each customer equals demand
    for j in customers:
        model.addConstr(
            gp.quicksum(ship[i, j] for i in facilities) == demand[j],
            name=f"demand_{j}"
        )

    # Capacity limits: total shipped from facility i <= capacity[i] * open[i]
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
        return {"objective": None, "status": f"solver_status_{model.Status}"}