import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["cost_matrix"]
    n = 5

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Assignment variables
    x = model.addVars(n, n, vtype=GRB.BINARY, name="x")

    # Bottleneck variable
    z = model.addVar(lb=0.0, name="z")

    # Objective: minimize the maximum assignment duration
    model.setObjective(z, GRB.MINIMIZE)

    # Each analyst assigned to exactly one incident
    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n)) == 1, name=f"analyst_{i}")

    # Each incident assigned to exactly one analyst
    for j in range(n):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n)) == 1, name=f"incident_{j}")

    # Bottleneck constraints: z >= cost of each selected assignment
    for i in range(n):
        for j in range(n):
            model.addConstr(z >= cost_matrix[i][j] * x[i, j], name=f"bottleneck_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}