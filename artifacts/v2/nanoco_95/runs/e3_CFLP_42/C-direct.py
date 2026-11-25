import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]   # list of 5
    capacity = params["capacity"]           # list of 5
    demand = params["demand"]               # list of 20
    transport_cost = params["transport_cost"]  # 20x5 (row=hospital, col=center)

    n_centers = 5
    n_hospitals = 20
    centers = range(n_centers)
    hospitals = range(n_hospitals)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # y[j] = 1 if center j is opened
    y = model.addVars(centers, vtype=GRB.BINARY, name="y")

    # x[i][j] = 1 if hospital i is assigned to center j
    x = model.addVars(hospitals, centers, vtype=GRB.BINARY, name="x")

    # Objective: fixed opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_cost[j] * y[j] for j in centers) +
        gp.quicksum(transport_cost[i][j] * demand[i] * x[i, j]
                    for i in hospitals for j in centers),
        GRB.MINIMIZE
    )

    # Each hospital assigned to exactly one center
    for i in hospitals:
        model.addConstr(gp.quicksum(x[i, j] for j in centers) == 1, name=f"single_source_{i}")

    # Capacity constraints
    for j in centers:
        model.addConstr(
            gp.quicksum(demand[i] * x[i, j] for i in hospitals) <= capacity[j] * y[j],
            name=f"capacity_{j}"
        )

    # Can only assign to open centers
    for i in hospitals:
        for j in centers:
            model.addConstr(x[i, j] <= y[j], name=f"open_link_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}