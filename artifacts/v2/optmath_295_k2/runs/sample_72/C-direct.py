import gurobipy as gp
from gurobipy import GRB

def solve(params):
    assignment_cost = params["assignment_cost"]
    employee_total_capacity = params["employee_total_capacity"]
    employee_project_limit = params["employee_project_limit"]
    project_demand = params["project_demand"]

    num_employees = 5
    num_projects = 5
    employees = range(num_employees)
    projects = range(num_projects)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(employees, projects, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(assignment_cost[i][j] * x[i, j] for i in employees for j in projects),
        GRB.MINIMIZE
    )

    for i in employees:
        model.addConstr(
            gp.quicksum(x[i, j] for j in projects) == employee_total_capacity[i],
            name=f"emp_capacity_{i}"
        )

    for j in projects:
        model.addConstr(
            gp.quicksum(x[i, j] for i in employees) == project_demand[j],
            name=f"proj_demand_{j}"
        )

    for i in employees:
        for j in projects:
            model.addConstr(
                x[i, j] <= employee_project_limit[i][j],
                name=f"proj_limit_{i}_{j}"
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