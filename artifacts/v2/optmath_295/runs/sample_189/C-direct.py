import gurobipy as gp
from gurobipy import GRB

def solve(params):
    consultant_capacity = params["consultant_capacity"]
    project_requirement = params["project_requirement"]
    cost = params["cost"]
    assignment_capacity = params["assignment_capacity"]

    num_consultants = 4
    num_projects = 5
    consultants = range(num_consultants)
    projects = range(num_projects)

    model = gp.Model("project_assignment")
    model.setParam("OutputFlag", 0)

    x = model.addVars(consultants, projects, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in consultants for j in projects),
        GRB.MINIMIZE
    )

    for i in consultants:
        model.addConstr(
            gp.quicksum(x[i, j] for j in projects) <= consultant_capacity[i],
            name=f"cap_consultant_{i}"
        )

    for j in projects:
        model.addConstr(
            gp.quicksum(x[i, j] for i in consultants) >= project_requirement[j],
            name=f"req_project_{j}"
        )

    for i in consultants:
        for j in projects:
            model.addConstr(
                x[i, j] <= assignment_capacity[i][j],
                name=f"assign_cap_{i}_{j}"
            )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}