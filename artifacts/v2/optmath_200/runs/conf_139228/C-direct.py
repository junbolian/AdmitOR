import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    shipping_cost = params["shipping_cost"]
    capacity = params["capacity"]

    n_facilities = len(fixed_cost)
    n_customers = len(demand)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    open_facility = model.addVars(n_facilities, vtype=GRB.BINARY, name="open")
    ship = model.addVars(n_facilities, n_customers, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    # Objective: minimize fixed costs + shipping costs
    model.setObjective(
        gp.quicksum(fixed_cost[i] * open_facility[i] for i in range(n_facilities)) +
        gp.quicksum(shipping_cost[i][j] * ship[i, j]
                    for i in range(n_facilities) for j in range(n_customers)),
        GRB.MINIMIZE
    )

    # Demand satisfaction constraints
    for j in range(n_customers):
        model.addConstr(
            gp.quicksum(ship[i, j] for i in range(n_facilities)) == demand[j],
            name=f"demand_{j}"
        )

    # Capacity constraints (only if facility is open)
    for i in range(n_facilities):
        model.addConstr(
            gp.quicksum(ship[i, j] for j in range(n_customers)) <= capacity[i] * open_facility[i],
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