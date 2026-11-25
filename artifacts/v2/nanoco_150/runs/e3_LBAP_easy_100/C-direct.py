import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["cost_matrix"]
    n = 6

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary assignment variables
    x = {}
    for i in range(n):
        for j in range(n):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Bottleneck variable
    z = model.addVar(vtype=GRB.CONTINUOUS, name="z", lb=0.0)

    model.setObjective(z, GRB.MINIMIZE)

    # Each machinist assigned exactly one job
    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n)) == 1, name=f"machinist_{i}")

    # Each job assigned to exactly one machinist
    for j in range(n):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n)) == 1, name=f"job_{j}")

    # z >= machining time for each assigned pair
    for i in range(n):
        for j in range(n):
            model.addConstr(z >= cost_matrix[i][j] * x[i, j], name=f"bottleneck_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}