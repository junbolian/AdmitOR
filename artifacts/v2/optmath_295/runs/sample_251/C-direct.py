import gurobipy as gp
from gurobipy import GRB


def solve(params):
    revenue = params["revenue"]
    demand = params["demand"]
    capacity = params["capacity"]

    n_packages = 11
    n_legs = 7

    # Structural constant: which packages utilize each flight leg
    leg_packages = [
        [2, 3, 4, 5, 7, 9],       # Leg 0
        [0, 2, 3, 4, 9, 10],      # Leg 1
        [7, 8, 10],               # Leg 2
        [2, 3, 5],                # Leg 3
        [1, 2, 4, 8, 9],          # Leg 4
        [3, 5, 6, 7, 8, 9],       # Leg 5
        [0, 1, 3, 4, 5, 9],       # Leg 6
    ]

    model = gp.Model("airline_revenue")
    model.Params.OutputFlag = 0

    x = model.addVars(n_packages, vtype=GRB.INTEGER, lb=0, name="x")

    # Demand constraints
    for j in range(n_packages):
        model.addConstr(x[j] <= demand[j], name=f"demand_{j}")

    # Capacity constraints
    for i in range(n_legs):
        model.addConstr(
            gp.quicksum(x[j] for j in leg_packages[i]) <= capacity[i],
            name=f"capacity_{i}",
        )

    model.setObjective(gp.quicksum(revenue[j] * x[j] for j in range(n_packages)), GRB.MAXIMIZE)

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}