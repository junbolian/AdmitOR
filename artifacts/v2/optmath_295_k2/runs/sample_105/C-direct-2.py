import gurobipy as gp
from gurobipy import GRB

def solve(params):
    revenue = params["revenue"]
    demand = params["demand"]
    leg_capacity = params["leg_capacity"]

    n_packages = 22
    n_legs = 20

    # Which packages use each leg
    leg_packages = {
        0:  [1, 2, 3, 5, 7, 8, 9, 12, 13, 14, 16, 19, 21],
        1:  [3, 4, 5, 6, 9, 14, 16, 17, 18, 20],
        2:  [0, 2, 3, 4, 5, 6, 8, 9, 11, 12, 13, 14, 15, 18, 19, 20, 21],
        3:  [4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 16, 18, 19, 21],
        4:  [3, 4, 8, 9, 10, 12, 15],
        5:  [0, 1, 2, 3, 4, 5, 6, 9, 10, 14, 16, 17, 18, 19, 20, 21],
        6:  [0, 5, 7, 8, 10, 11, 14, 17, 18, 20],
        7:  [0, 7, 10, 12, 13, 18, 19, 20, 21],
        8:  [3, 7, 8, 9, 10, 13, 15, 17, 19, 20],
        9:  [0, 3, 5, 6, 9, 10, 11, 14, 15, 16],
        10: [0, 1, 5, 6, 9, 11, 12, 19, 20],
        11: [2, 6, 9, 10, 12, 14, 15, 16, 18, 19],
        12: [0, 1, 2, 3, 5, 8, 9, 10, 12, 15, 17, 18, 19, 21],
        13: [0, 1, 4, 5, 8, 9, 11, 15, 16, 17, 18],
        14: [5, 6, 8, 11, 12, 14, 15, 16],
        15: [1, 3, 10, 12, 13, 15, 16, 18],
        16: [1, 4, 5, 6, 7, 8, 11, 12, 15, 18, 20, 21],
        17: [4, 6, 7, 8, 11, 12, 13, 14, 17, 19, 20, 21],
        18: [4, 8, 10, 11, 12, 16, 20],
        19: [1, 2, 6, 7, 8, 9, 10, 11, 12, 14, 16, 20, 21],
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_packages, vtype=GRB.INTEGER, lb=0, name="x")

    # Objective: maximize revenue
    model.setObjective(
        gp.quicksum(revenue[p] * x[p] for p in range(n_packages)),
        GRB.MAXIMIZE
    )

    # Demand constraints
    for p in range(n_packages):
        model.addConstr(x[p] <= demand[p], name=f"demand_{p}")

    # Leg capacity constraints
    for leg in range(n_legs):
        pkgs = leg_packages[leg]
        model.addConstr(
            gp.quicksum(x[p] for p in pkgs) <= leg_capacity[leg],
            name=f"leg_{leg}"
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
        return {"objective": None, "status": f"gurobi_status_{status}"}