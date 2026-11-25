import gurobipy as gp
from gurobipy import GRB

def solve(params):
    employee_availability = params["employee_availability"]
    project_requirement = params["project_requirement"]
    assignment_cost = params["assignment_cost"]
    per_assignment_capacity = params["per_assignment_capacity"]

    num_employees = len(employee_availability)
    num_projects = len(project_requirement)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_employees, num_projects, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(
            assignment_cost[i][j] * x[i, j]
            for i in range(num_employees)
            for j in range(num_projects)
        ),
        GRB.MINIMIZE
    )

    for i in range(num_employees):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_projects)) == employee_availability[i],
            name=f"supply_{i}"
        )

    for j in range(num_projects):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_employees)) == project_requirement[j],
            name=f"demand_{j}"
        )

    for i in range(num_employees):
        for j in range(num_projects):
            model.addConstr(
                x[i, j] <= per_assignment_capacity[i][j],
                name=f"cap_{i}_{j}"
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