import gurobipy as gp
from gurobipy import GRB

def solve(params):
    employee_availability = params["employee_availability"]
    project_requirement = params["project_requirement"]
    assignment_cost = params["assignment_cost"]
    assignment_capacity = params["assignment_capacity"]

    num_employees = 6
    num_projects = 6
    employees = range(num_employees)
    projects = range(num_projects)

    model = gp.Model("employee_project_assignment")
    model.setParam("OutputFlag", 0)

    x = model.addVars(employees, projects, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(assignment_cost[i][j] * x[i, j] for i in employees for j in projects),
        GRB.MINIMIZE
    )

    for i in employees:
        model.addConstr(
            gp.quicksum(x[i, j] for j in projects) == employee_availability[i],
            name=f"availability_{i}"
        )

    for j in projects:
        model.addConstr(
            gp.quicksum(x[i, j] for i in employees) == project_requirement[j],
            name=f"requirement_{j}"
        )

    for i in employees:
        for j in projects:
            model.addConstr(
                x[i, j] <= assignment_capacity[i][j],
                name=f"capacity_{i}_{j}"
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