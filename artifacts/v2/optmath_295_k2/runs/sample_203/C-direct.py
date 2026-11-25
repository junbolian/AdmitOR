import gurobipy as gp
from gurobipy import GRB


def solve(params):
    consultant_hours = params["consultant_hours"]
    project_hours = params["project_hours"]
    capacity = params["capacity"]
    cost = params["cost"]

    n_cons = len(consultant_hours)
    n_proj = len(project_hours)

    model = gp.Model("consultant_assignment")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(n_cons):
        for j in range(n_proj):
            x[i, j] = model.addVar(
                lb=0.0,
                ub=float(capacity[i][j]),
                obj=float(cost[i][j]),
                name=f"x_{i}_{j}",
            )

    model.modelSense = GRB.MINIMIZE

    for i in range(n_cons):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_proj)) == float(consultant_hours[i]),
            name=f"consultant_hours_{i}",
        )

    for j in range(n_proj):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_cons)) == float(project_hours[j]),
            name=f"project_hours_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"status_{model.status}"}