import gurobipy as gp
from gurobipy import GRB

def solve(params):
    revenue = params["revenue"]
    demand = params["demand"]
    capacity = params["capacity"]

    # Resource-to-package membership
    resource_packages = [
        [2, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 22, 24],
        [0, 1, 2, 4, 6, 7, 8, 9, 10, 11, 12, 14, 16, 17, 19, 20, 21, 22, 23, 24],
        [0, 1, 5, 6, 8, 9, 13, 14, 15, 16, 17, 19, 23],
        [0, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 15, 17, 18, 19, 20, 21, 22, 23, 24],
        [1, 2, 3, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 19, 20, 22, 23],
        [1, 2, 6, 9, 10, 12, 14, 15, 16, 17, 18, 19, 21, 22, 23],
        [0, 1, 2, 3, 4, 5, 7, 9, 10, 11, 12, 14, 15, 16, 17, 19, 20, 22, 23],
        [0, 1, 2, 5, 6, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 24],
        [1, 2, 4, 5, 6, 8, 10, 12, 13, 14, 16, 17, 18, 19, 20, 22, 23],
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 18, 20, 21, 22],
        [0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 14, 17, 18, 20, 21, 22, 23, 24],
        [0, 4, 6, 7, 9, 10, 13, 14, 15, 18, 19, 20, 21, 22, 24],
        [1, 2, 3, 4, 6, 7, 8, 9, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24],
        [0, 1, 2, 3, 4, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24],
        [0, 1, 2, 3, 4, 5, 6, 9, 10, 13, 14, 15, 17, 18, 21, 23],
    ]

    n_packages = 25
    n_resources = 15

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_packages, lb=0.0, name="x")

    # Demand constraints
    for i in range(n_packages):
        model.addConstr(x[i] <= demand[i], name=f"demand_{i}")

    # Capacity constraints
    for r in range(n_resources):
        model.addConstr(
            gp.quicksum(x[i] for i in resource_packages[r]) <= capacity[r],
            name=f"capacity_{r}"
        )

    # Objective
    model.setObjective(
        gp.quicksum(revenue[i] * x[i] for i in range(n_packages)),
        GRB.MAXIMIZE
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