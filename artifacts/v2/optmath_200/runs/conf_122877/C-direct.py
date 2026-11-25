import gurobipy as gp
from gurobipy import GRB

def solve(params):
    employee_availability = params["employee_availability"]
    project_requirements = params["project_requirements"]
    assignment_costs = params["assignment_costs"]
    capacity_limits = params["capacity_limits"]

    num_employees = len(employee_availability)
    num_projects = len(project_requirements)

    model = gp.Model("employee_project_assignment")
    model.setParam("OutputFlag", 0)

    # Decision variables: hours employee i assigned to project j
    x = {}
    for i in range(num_employees):
        for j in range(num_projects):
            x[i, j] = model.addVar(
                lb=0.0,
                ub=capacity_limits[i][j],
                vtype=GRB.CONTINUOUS,
                name=f"x_{i}_{j}"
            )

    # Objective: minimize total assignment cost
    model.setObjective(
        gp.quicksum(assignment_costs[i][j] * x[i, j]
                    for i in range(num_employees)
                    for j in range(num_projects)),
        GRB.MINIMIZE
    )

    # Employee availability constraints: total hours per employee equals availability
    for i in range(num_employees):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_projects)) == employee_availability[i],
            name=f"availability_{i}"
        )

    # Project requirement constraints: total hours per project equals requirement
    for j in range(num_projects):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_employees)) == project_requirements[j],
            name=f"requirement_{j}"
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