import gurobipy as gp
from gurobipy import GRB

def solve(params):
    revenue = params["revenue"]
    demand = params["demand"]
    flight_capacity = params["flight_capacity"]

    num_packages = 21
    num_legs = 18

    # Flight leg to package membership
    leg_packages = [
        [0, 2, 4, 7, 11, 12, 16, 17, 19],
        [0, 1, 7, 9, 10, 11, 15, 20],
        [0, 1, 3, 4, 7, 11, 13, 15, 17, 19],
        [6, 7, 9, 15, 16, 17, 18, 19],
        [2, 3, 4, 5, 7, 11, 12, 13, 15, 16, 17, 19, 20],
        [0, 1, 3, 4, 5, 6, 8, 9, 10, 12, 14, 18],
        [1, 4, 5, 7, 8, 10, 13, 14, 16, 17, 18, 19, 20],
        [0, 1, 2, 4, 8, 9, 11, 13, 14, 15, 16, 17, 18, 19, 20],
        [0, 5, 9, 10, 12, 14, 15, 16, 20],
        [2, 4, 5, 6, 7, 8, 9, 10, 11, 16, 18, 19],
        [2, 6, 12, 15, 17, 18],
        [1, 10, 13, 14, 15, 19],
        [1, 2, 4, 5, 6, 8, 9, 11, 13, 14, 17, 18, 20],
        [0, 1, 4, 5, 7, 8, 9, 10, 14, 16, 17, 19],
        [0, 1, 2, 3, 7, 9, 11, 14, 16, 18, 19],
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 13, 15, 19],
        [2, 6, 8, 9, 12, 13, 16, 17, 19, 20],
        [1, 2, 3, 6, 7, 10, 11, 14, 18],
    ]

    model = gp.Model("vacation_packages")
    model.setParam("OutputFlag", 0)

    sell = model.addVars(num_packages, vtype=GRB.INTEGER, lb=0, name="Sell")

    # Objective: maximize revenue
    model.setObjective(
        gp.quicksum(revenue[p] * sell[p] for p in range(num_packages)),
        GRB.MAXIMIZE
    )

    # Demand constraints
    for p in range(num_packages):
        model.addConstr(sell[p] <= demand[p], name=f"demand_{p}")

    # Flight leg capacity constraints
    for leg in range(num_legs):
        model.addConstr(
            gp.quicksum(sell[p] for p in leg_packages[leg]) <= flight_capacity[leg],
            name=f"leg_{leg}"
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