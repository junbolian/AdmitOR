import gurobipy as gp
from gurobipy import GRB

def solve(params):
    revenue = params["revenue"]
    demand_limit = params["demand_limit"]
    flight_capacity = params["flight_capacity"]

    # Flight leg to package membership
    leg_packages = {
        0: [1, 2, 4, 5, 6, 7],
        1: [0, 2, 4, 6, 8, 9, 10],
        2: [2, 3, 4, 10],
        3: [1, 6, 7, 10],
        4: [1, 3, 6, 7, 8, 9],
    }

    num_packages = 11
    num_legs = 5

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_packages, vtype=GRB.INTEGER, lb=0, name="x")

    # Objective: maximize revenue
    model.setObjective(
        gp.quicksum(revenue[j] * x[j] for j in range(num_packages)),
        GRB.MAXIMIZE
    )

    # Demand constraints
    for j in range(num_packages):
        model.addConstr(x[j] <= demand_limit[j], name=f"demand_{j}")

    # Flight leg capacity constraints
    for leg in range(num_legs):
        model.addConstr(
            gp.quicksum(x[j] for j in leg_packages[leg]) <= flight_capacity[leg],
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
        return {"objective": None, "status": f"status_{status}"}