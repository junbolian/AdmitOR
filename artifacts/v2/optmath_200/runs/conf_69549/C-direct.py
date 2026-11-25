import gurobipy as gp
from gurobipy import GRB

def solve(params):
    revenue = params["revenue"]
    demand = params["demand"]
    flight_capacity = params["flight_capacity"]

    # Flight leg to package membership
    leg_packages = {
        0: [0, 1, 2, 3, 6, 7, 9],
        1: [0, 1, 4, 6],
        2: [1, 5, 8, 9],
        3: [0, 1, 4, 8],
        4: [1, 3, 4],
        5: [0, 2, 5],
        6: [2, 3, 4, 7, 8],
    }

    n_packages = 10
    n_legs = 7

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_packages, vtype=GRB.INTEGER, lb=0, name="x")

    # Demand constraints
    for i in range(n_packages):
        model.addConstr(x[i] <= demand[i], name=f"demand_{i}")

    # Flight capacity constraints
    for leg in range(n_legs):
        model.addConstr(
            gp.quicksum(x[p] for p in leg_packages[leg]) <= flight_capacity[leg],
            name=f"capacity_{leg}"
        )

    # Objective
    model.setObjective(
        gp.quicksum(revenue[i] * x[i] for i in range(n_packages)),
        GRB.MAXIMIZE
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