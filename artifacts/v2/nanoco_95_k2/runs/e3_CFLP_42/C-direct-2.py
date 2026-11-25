import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    num_hospitals = len(demand)
    num_centers = len(opening_cost)

    I = range(num_hospitals)
    J = range(num_centers)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # y[j] = 1 if center j is opened
    y = model.addVars(J, vtype=GRB.BINARY, name="y")

    # x[i,j] = 1 if hospital i is assigned to center j
    x = model.addVars(I, J, vtype=GRB.BINARY, name="x")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_cost[j] * y[j] for j in J) +
        gp.quicksum(transport_cost[i][j] * demand[i] * x[i, j] for i in I for j in J),
        GRB.MINIMIZE
    )

    # Each hospital assigned to exactly one center
    for i in I:
        model.addConstr(gp.quicksum(x[i, j] for j in J) == 1, name=f"assign_{i}")

    # Capacity constraints
    for j in J:
        model.addConstr(
            gp.quicksum(demand[i] * x[i, j] for i in I) <= capacity[j] * y[j],
            name=f"capacity_{j}"
        )

    # Can only assign to open center
    for i in I:
        for j in J:
            model.addConstr(x[i, j] <= y[j], name=f"link_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}