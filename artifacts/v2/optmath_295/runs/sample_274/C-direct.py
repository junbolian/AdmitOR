import gurobipy as gp
from gurobipy import GRB

def solve(params):
    revenues = params["revenues"]
    demand_limits = params["demand_limits"]
    leg_capacities = params["leg_capacities"]

    # Leg-to-package membership (structural, from problem description)
    leg_packages = {
        0: [1, 2, 4, 5, 6, 7],
        1: [0, 2, 4, 6, 8, 9, 10],
        2: [2, 3, 4, 10],
        3: [1, 6, 7, 10],
        4: [1, 3, 6, 7, 8, 9],
    }

    n_packages = 11
    n_legs = 5

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_packages, vtype=GRB.INTEGER, lb=0, name="x")

    # Objective: maximize total revenue
    model.setObjective(
        gp.quicksum(revenues[j] * x[j] for j in range(n_packages)),
        GRB.MAXIMIZE
    )

    # Demand limit constraints
    for j in range(n_packages):
        model.addConstr(x[j] <= demand_limits[j], name=f"demand_{j}")

    # Flight leg capacity constraints
    for leg in range(n_legs):
        model.addConstr(
            gp.quicksum(x[j] for j in leg_packages[leg]) <= leg_capacities[leg],
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