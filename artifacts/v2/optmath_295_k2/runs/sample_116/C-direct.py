import gurobipy as gp
from gurobipy import GRB


def solve(params):
    consultant_availability = params["consultant_availability"]
    project_demand = params["project_demand"]
    assignment_cost = params["assignment_cost"]
    assignment_capacity = params["assignment_capacity"]

    num_consultants = len(consultant_availability)
    num_projects = len(project_demand)

    model = gp.Model("project_assignment")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(num_consultants):
        for j in range(num_projects):
            x[i, j] = model.addVar(
                lb=0.0,
                ub=assignment_capacity[i][j],
                obj=assignment_cost[i][j],
                name=f"x_{i}_{j}",
            )

    model.ModelSense = GRB.MINIMIZE

    for i in range(num_consultants):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_projects))
            == consultant_availability[i],
            name=f"supply_{i}",
        )

    for j in range(num_projects):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_consultants))
            == project_demand[j],
            name=f"demand_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}