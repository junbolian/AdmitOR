import gurobipy as gp
from gurobipy import GRB

def solve(params):
    revenue = params["revenue"]
    demand = params["demand"]
    capacity = params["capacity"]

    # Package-to-leg membership
    leg_packages = {
        0: [0, 8, 10],
        1: [1, 2, 4, 5, 6, 8, 9],
        2: [2, 3, 5, 6, 7, 8],
        3: [2, 6, 7, 8, 10],
        4: [1, 2, 9, 10],
        5: [2, 4, 5, 6, 8, 9],
        6: [0, 1, 3, 4, 5, 7, 8, 9],
    }

    num_packages = 11
    num_legs = 7

    model = gp.Model("airline_revenue_management")
    model.setParam("OutputFlag", 0)

    # Decision variables: integer units sold for each package
    x = model.addVars(num_packages, vtype=GRB.INTEGER, lb=0, name="x")

    # Objective: maximize total revenue
    model.setObjective(
        gp.quicksum(revenue[p] * x[p] for p in range(num_packages)),
        GRB.MAXIMIZE
    )

    # Demand constraints
    for p in range(num_packages):
        model.addConstr(x[p] <= demand[p], name=f"demand_{p}")

    # Capacity constraints
    for leg in range(num_legs):
        model.addConstr(
            gp.quicksum(x[p] for p in leg_packages[leg]) <= capacity[leg],
            name=f"capacity_{leg}"
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