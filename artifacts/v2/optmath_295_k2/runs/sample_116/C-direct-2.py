import gurobipy as gp
from gurobipy import GRB


def solve(params):
    consultant_availability = params["consultant_availability"]
    project_demand = params["project_demand"]
    assignment_cost = params["assignment_cost"]
    assignment_capacity = params["assignment_capacity"]

    num_consultants = len(consultant_availability)
    num_projects = len(project_demand)

    consultants = range(num_consultants)
    projects = range(num_projects)

    model = gp.Model("project_assignment")
    model.setParam("OutputFlag", 0)

    x = model.addVars(
        consultants,
        projects,
        lb=0.0,
        name="x"
    )

    # Capacity constraints
    for i in consultants:
        for j in projects:
            x[i, j].ub = assignment_capacity[i][j]

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(
            assignment_cost[i][j] * x[i, j]
            for i in consultants
            for j in projects
        ),
        GRB.MINIMIZE
    )

    # Supply constraints: total hours per consultant equals availability
    for i in consultants:
        model.addConstr(
            gp.quicksum(x[i, j] for j in projects) == consultant_availability[i],
            name=f"supply_{i}"
        )

    # Demand constraints: total hours per project equals requirement
    for j in projects:
        model.addConstr(
            gp.quicksum(x[i, j] for i in consultants) == project_demand[j],
            name=f"demand_{j}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}