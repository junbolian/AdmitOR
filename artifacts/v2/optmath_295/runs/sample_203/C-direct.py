import gurobipy as gp
from gurobipy import GRB

def solve(params):
    consultant_hours = params["consultant_hours"]
    project_hours = params["project_hours"]
    capacity = params["capacity"]
    cost = params["cost"]

    num_consultants = len(consultant_hours)
    num_projects = len(project_hours)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_consultants, num_projects, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(num_consultants) for j in range(num_projects)),
        GRB.MINIMIZE
    )

    for i in range(num_consultants):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_projects)) == consultant_hours[i],
            name=f"consultant_{i}"
        )

    for j in range(num_projects):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_consultants)) == project_hours[j],
            name=f"project_{j}"
        )

    for i in range(num_consultants):
        for j in range(num_projects):
            model.addConstr(x[i, j] <= capacity[i][j], name=f"cap_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}