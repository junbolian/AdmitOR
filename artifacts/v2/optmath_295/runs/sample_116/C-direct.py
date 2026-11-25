import gurobipy as gp
from gurobipy import GRB


def solve(params):
    consultant_availability = params["consultant_availability"]
    project_requirements = params["project_requirements"]
    assignment_costs = params["assignment_costs"]
    assignment_capacity = params["assignment_capacity"]

    num_consultants = len(consultant_availability)
    num_projects = len(project_requirements)

    consultants = range(num_consultants)
    projects = range(num_projects)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(consultants, projects, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    model.setObjective(
        gp.quicksum(
            assignment_costs[i][j] * x[i, j]
            for i in consultants
            for j in projects
        ),
        GRB.MINIMIZE,
    )

    # Supply constraints: each consultant's total hours equals their availability
    for i in consultants:
        model.addConstr(
            gp.quicksum(x[i, j] for j in projects) == consultant_availability[i],
            name=f"supply_{i}",
        )

    # Demand constraints: each project receives exactly its required hours
    for j in projects:
        model.addConstr(
            gp.quicksum(x[i, j] for i in consultants) == project_requirements[j],
            name=f"demand_{j}",
        )

    # Capacity constraints: hours assigned cannot exceed per-pair capacity
    for i in consultants:
        for j in projects:
            model.addConstr(
                x[i, j] <= assignment_capacity[i][j],
                name=f"cap_{i}_{j}",
            )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}