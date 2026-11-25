import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["cost_matrix"]
    num_workers = len(cost_matrix)
    num_tasks = len(cost_matrix[0])

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_workers, num_tasks, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j] for i in range(num_workers) for j in range(num_tasks)),
        GRB.MINIMIZE
    )

    for i in range(num_workers):
        model.addConstr(gp.quicksum(x[i, j] for j in range(num_tasks)) == 1, name=f"worker_{i}")

    for j in range(num_tasks):
        model.addConstr(gp.quicksum(x[i, j] for i in range(num_workers)) == 1, name=f"task_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}