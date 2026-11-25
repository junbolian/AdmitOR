import gurobipy as gp
from gurobipy import GRB

def solve(params):
    revenue = params["revenue"]
    demand_limit = params["demand_limit"]
    capacity_limit = params["capacity_limit"]

    # Package indices for each capacity constraint (structural constants)
    capacity_packages = [
        [0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19, 21, 22, 23],
        [0, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 15, 17, 18, 19, 20, 21, 22],
        [0, 1, 2, 3, 4, 5, 6, 8, 9, 11, 13, 14, 15, 17, 18, 19, 20, 22, 23],
        [1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 18, 19, 20, 21, 23],
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
        [0, 1, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 22, 23],
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
        [0, 2, 5, 6, 7, 8, 9, 11, 12, 13, 15, 17, 20, 21, 23],
        [1, 2, 3, 5, 7, 8, 9, 11, 12, 13, 14, 15, 17, 19, 20, 21, 23],
        [2, 3, 4, 5, 6, 9, 11, 12, 14, 15, 16, 18, 19, 20, 21, 23],
        [0, 2, 3, 4, 5, 6, 7, 9, 11, 12, 13, 14, 16, 17, 18, 19, 20, 21, 22],
        [0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
        [0, 1, 3, 4, 6, 7, 8, 9, 10, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
        [0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 17, 18, 19, 20, 21, 22, 23],
        [0, 1, 8, 9, 10, 11, 13, 15, 16, 17, 18, 19, 20, 22, 23],
    ]

    n_packages = 24
    n_constraints = 15

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_packages, lb=0.0, vtype=GRB.INTEGER, name="x")

    # Objective: maximize total revenue
    model.setObjective(
        gp.quicksum(revenue[i] * x[i] for i in range(n_packages)),
        GRB.MAXIMIZE
    )

    # Demand constraints
    for i in range(n_packages):
        model.addConstr(x[i] <= demand_limit[i], name=f"demand_{i}")

    # Capacity constraints
    for c in range(n_constraints):
        model.addConstr(
            gp.quicksum(x[i] for i in capacity_packages[c]) <= capacity_limit[c],
            name=f"capacity_{c}"
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