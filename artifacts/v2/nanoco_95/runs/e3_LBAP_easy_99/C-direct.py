import gurobipy as gp
from gurobipy import GRB

def solve(params):
    duration_matrix = params["duration_matrix"]
    n = 5

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Assignment variables: x[i,j] = 1 if analyst i handles incident j
    x = {}
    for i in range(n):
        for j in range(n):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Bottleneck variable: maximum duration across all assignments
    z = model.addVar(vtype=GRB.CONTINUOUS, name="z", lb=0.0)

    model.setObjective(z, GRB.MINIMIZE)

    # Each analyst assigned exactly one incident
    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n)) == 1, name=f"analyst_{i}")

    # Each incident assigned to exactly one analyst
    for j in range(n):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n)) == 1, name=f"incident_{j}")

    # z >= duration of each active assignment
    for i in range(n):
        for j in range(n):
            model.addConstr(z >= duration_matrix[i][j] * x[i, j], name=f"bottleneck_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}