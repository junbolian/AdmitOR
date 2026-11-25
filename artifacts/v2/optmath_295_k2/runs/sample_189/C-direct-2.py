import gurobipy as gp
from gurobipy import GRB


def solve(params):
    consultant_availability = params["consultant_availability"]
    project_requirements = params["project_requirements"]
    cost_matrix = params["cost_matrix"]
    assignment_capacity = params["assignment_capacity"]

    num_consultants = len(consultant_availability)
    num_projects = len(project_requirements)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_consultants, num_projects, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(
            cost_matrix[i][j] * x[i, j]
            for i in range(num_consultants)
            for j in range(num_projects)
        ),
        GRB.MINIMIZE,
    )

    # Consultant availability constraints
    for i in range(num_consultants):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_projects)) <= consultant_availability[i],
            name=f"avail_{i}",
        )

    # Project requirement constraints
    for j in range(num_projects):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_consultants)) >= project_requirements[j],
            name=f"req_{j}",
        )

    # Per-assignment capacity constraints
    for i in range(num_consultants):
        for j in range(num_projects):
            model.addConstr(
                x[i, j] <= assignment_capacity[i][j],
                name=f"cap_{i}_{j}",
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