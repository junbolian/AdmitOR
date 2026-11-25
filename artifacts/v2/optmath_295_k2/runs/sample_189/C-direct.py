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

    # Decision variables: hours consultant i assigns to project j
    x = model.addVars(num_consultants, num_projects, lb=0.0, name="x")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(
            cost_matrix[i][j] * x[i, j]
            for i in range(num_consultants)
            for j in range(num_projects)
        ),
        GRB.MINIMIZE
    )

    # Constraint 1: each project's requirements must be met
    for j in range(num_projects):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_consultants)) == project_requirements[j],
            name=f"project_req_{j}"
        )

    # Constraint 2: each consultant cannot exceed their total available hours
    for i in range(num_consultants):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_projects)) <= consultant_availability[i],
            name=f"consultant_avail_{i}"
        )

    # Constraint 3: per-consultant per-project capacity limits
    for i in range(num_consultants):
        for j in range(num_projects):
            model.addConstr(
                x[i, j] <= assignment_capacity[i][j],
                name=f"cap_{i}_{j}"
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