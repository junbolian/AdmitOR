import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    shipping_cost = params["shipping_cost"]

    n_facilities = len(fixed_cost)
    n_customers = len(demand)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    # y[j] = 1 if facility j is opened
    y = model.addVars(n_facilities, vtype=GRB.BINARY, name="y")
    # x[i][j] = units shipped from facility j to customer i
    x = model.addVars(n_customers, n_facilities, vtype=GRB.CONTINUOUS, lb=0.0, name="x")

    # Objective: minimize fixed costs + shipping costs
    model.setObjective(
        gp.quicksum(fixed_cost[j] * y[j] for j in range(n_facilities)) +
        gp.quicksum(shipping_cost[i][j] * x[i, j] for i in range(n_customers) for j in range(n_facilities)),
        GRB.MINIMIZE
    )

    # Demand satisfaction constraints
    for i in range(n_customers):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_facilities)) == demand[i],
            name=f"demand_{i}"
        )

    # Capacity constraints
    for j in range(n_facilities):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_customers)) <= capacity[j] * y[j],
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