import gurobipy as gp
from gurobipy import GRB


def solve(params):
    availability = params["availability"]
    project_requirement = params["project_requirement"]
    assignment_cost = params["assignment_cost"]
    per_project_limit = params["per_project_limit"]

    n_persons = 7
    n_projects = 7

    model = gp.Model("workforce_allocation")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(n_persons):
        for j in range(n_projects):
            x[i, j] = model.addVar(
                lb=0.0,
                ub=per_project_limit[i][j],
                name=f"x_{i}_{j}",
            )

    model.setObjective(
        gp.quicksum(
            assignment_cost[i][j] * x[i, j]
            for i in range(n_persons)
            for j in range(n_projects)
        ),
        GRB.MINIMIZE,
    )

    # Each person's total assigned hours must not exceed their availability.
    for i in range(n_persons):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_projects)) <= availability[i],
            name=f"avail_{i}",
        )

    # Each project's total assigned hours must meet its requirement.
    for j in range(n_projects):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_persons)) >= project_requirement[j],
            name=f"req_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": f"status_{model.status}"}