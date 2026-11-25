import gurobipy as gp
from gurobipy import GRB

def solve(params):
    employee_availability = params["employee_availability"]
    project_requirements = params["project_requirements"]
    assignment_costs = params["assignment_costs"]
    pair_capacities = params["pair_capacities"]

    num_employees = 8
    num_projects = 9
    employees = range(num_employees)
    projects = range(num_projects)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_employees, num_projects, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(
            assignment_costs[i][j] * x[i, j]
            for i in employees
            for j in projects
        ),
        GRB.MINIMIZE
    )

    for i in employees:
        model.addConstr(
            gp.quicksum(x[i, j] for j in projects) <= employee_availability[i],
            name=f"avail_{i}"
        )

    for j in projects:
        model.addConstr(
            gp.quicksum(x[i, j] for i in employees) == project_requirements[j],
            name=f"req_{j}"
        )

    for i in employees:
        for j in projects:
            model.addConstr(
                x[i, j] <= pair_capacities[i][j],
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