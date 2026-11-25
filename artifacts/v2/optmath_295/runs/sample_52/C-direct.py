import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]   # list of length 4
    demand     = params["demand"]       # list of length 10
    capacity   = params["capacity"]     # list of length 4

    num_facilities = 4
    num_customers  = 10

    # Variable serving costs (facility x customer), read from problem description
    # but NOT in params, so they are structural constants embedded here.
    # Rows = facilities 0-3, Cols = customers 0-9
    serve_cost = [
        [34, 32, 30, 33, 28, 29, 27, 31, 30, 35],
        [26, 28, 25, 29, 27, 31, 30, 28, 33, 32],
        [32, 30, 28, 27, 29, 26, 31, 33, 25, 30],
        [32, 31, 29, 28, 30, 27, 33, 26, 32, 29],
    ]

    facilities = range(num_facilities)
    customers  = range(num_customers)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: open facility i
    open_fac = model.addVars(facilities, vtype=GRB.BINARY, name="open")

    # Continuous: amount served from facility i to customer j
    alloc = model.addVars(facilities, customers, lb=0.0, name="alloc")

    # Objective: fixed costs + variable serving costs
    model.setObjective(
        gp.quicksum(fixed_cost[i] * open_fac[i] for i in facilities) +
        gp.quicksum(serve_cost[i][j] * alloc[i, j] for i in facilities for j in customers),
        GRB.MINIMIZE
    )

    # Demand satisfaction
    for j in customers:
        model.addConstr(
            gp.quicksum(alloc[i, j] for i in facilities) == demand[j],
            name=f"demand_{j}"
        )

    # Capacity constraints
    for i in facilities:
        model.addConstr(
            gp.quicksum(alloc[i, j] for j in customers) <= capacity[i] * open_fac[i],
            name=f"capacity_{i}"
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