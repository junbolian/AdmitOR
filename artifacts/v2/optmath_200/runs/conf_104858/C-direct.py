import gurobipy as gp
from gurobipy import GRB

def solve(params):
    revenue = params["revenue"]
    demand = params["demand"]
    flight_capacity = params["flight_capacity"]

    # Flight leg to package membership (structural, from problem description)
    flight_packages = {
        0: [0, 1, 5, 6, 11, 15, 16],
        1: [1, 8, 16],
        2: [0, 2, 3, 8, 11, 16],
        3: [4, 5, 6, 7, 13, 16],
        4: [1, 2, 4, 5, 6, 8, 11, 12, 13],
    }

    n_packages = 17
    n_legs = 5

    model = gp.Model("vacation_packages")
    model.setParam("OutputFlag", 0)

    # Decision variables: integer units sold per package
    x = model.addVars(n_packages, vtype=GRB.INTEGER, lb=0, name="x")

    # Objective: maximize total revenue
    model.setObjective(
        gp.quicksum(revenue[i] * x[i] for i in range(n_packages)),
        GRB.MAXIMIZE
    )

    # Demand constraints
    for i in range(n_packages):
        model.addConstr(x[i] <= demand[i], name=f"demand_{i}")

    # Flight leg capacity constraints
    for leg in range(n_legs):
        pkgs = flight_packages[leg]
        model.addConstr(
            gp.quicksum(x[p] for p in pkgs) <= flight_capacity[leg],
            name=f"flight_{leg}"
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
        return {"objective": None, "status": f"status_{status}"}