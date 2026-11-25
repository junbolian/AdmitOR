import gurobipy as gp
from gurobipy import GRB


def solve(params):
    employee_availability = params["employee_availability"]
    project_requirements = params["project_requirements"]
    assignment_costs = params["assignment_costs"]
    assignment_limits = params["assignment_limits"]

    num_employees = len(employee_availability)
    num_projects = len(project_requirements)

    employees = range(num_employees)
    projects = range(num_projects)

    model = gp.Model("personnel_assignment")
    model.setParam("OutputFlag", 0)

    # Decision variables: hours employee i spends on project j
    x = model.addVars(
        employees,
        projects,
        lb=0.0,
        name="x"
    )

    # Objective: minimize total assignment cost
    model.setObjective(
        gp.quicksum(
            assignment_costs[i][j] * x[i, j]
            for i in employees
            for j in projects
        ),
        GRB.MINIMIZE
    )

    # Employee availability constraints
    for i in employees:
        model.addConstr(
            gp.quicksum(x[i, j] for j in projects) <= employee_availability[i],
            name=f"avail_{i}"
        )

    # Project requirement constraints (exact)
    for j in projects:
        model.addConstr(
            gp.quicksum(x[i, j] for i in employees) == project_requirements[j],
            name=f"req_{j}"
        )

    # Assignment limit constraints
    for i in employees:
        for j in projects:
            model.addConstr(
                x[i, j] <= assignment_limits[i][j],
                name=f"limit_{i}_{j}"
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