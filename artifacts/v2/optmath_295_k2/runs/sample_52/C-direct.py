import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]      # list of 4 floats
    demand = params["demand"]              # list of 10 floats
    capacity = params["capacity"]          # list of 4 floats
    variable_cost = params["variable_cost"]  # 4x10 list of lists

    num_facilities = 4
    num_customers = 10
    facilities = range(num_facilities)
    customers = range(num_customers)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: open facility i
    open_facility = model.addVars(facilities, vtype=GRB.BINARY, name="open")

    # Continuous: units served from facility i to customer j
    alloc = model.addVars(facilities, customers, lb=0.0, name="alloc")

    # Objective: fixed costs + variable costs
    model.setObjective(
        gp.quicksum(fixed_cost[i] * open_facility[i] for i in facilities) +
        gp.quicksum(variable_cost[i][j] * alloc[i, j] for i in facilities for j in customers),
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
            gp.quicksum(alloc[i, j] for j in customers) <= capacity[i] * open_facility[i],
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