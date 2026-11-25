import gurobipy as gp
from gurobipy import GRB

def solve(params):
    consultant_availability = params["consultant_availability"]
    project_requirements = params["project_requirements"]
    assignment_cost = params["assignment_cost"]
    assignment_limits = params["assignment_limits"]

    num_consultants = len(consultant_availability)
    num_projects = len(project_requirements)

    model = gp.Model("project_assignment")
    model.setParam("OutputFlag", 0)

    # Decision variables: hours consultant i works on project j
    x = model.addVars(num_consultants, num_projects, lb=0.0, name="x")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(
            assignment_cost[i][j] * x[i, j]
            for i in range(num_consultants)
            for j in range(num_projects)
        ),
        GRB.MINIMIZE
    )

    # Constraint 1: consultant availability
    for i in range(num_consultants):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_projects)) <= consultant_availability[i],
            name=f"avail_{i}"
        )

    # Constraint 2: project requirements (exactly)
    for j in range(num_projects):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_consultants)) == project_requirements[j],
            name=f"req_{j}"
        )

    # Constraint 3: assignment limits
    for i in range(num_consultants):
        for j in range(num_projects):
            model.addConstr(
                x[i, j] <= assignment_limits[i][j],
                name=f"limit_{i}_{j}"
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