import gurobipy as gp
from gurobipy import GRB

def solve(params):
    employee_availability = params["employee_availability"]
    project_requirement = params["project_requirement"]
    assignment_cost = params["assignment_cost"]
    assignment_capacity = params["assignment_capacity"]

    num_employees = 6
    num_projects = 6

    model = gp.Model("employee_project_assignment")
    model.Params.OutputFlag = 0

    # Decision variables: hours employee i spends on project j
    x = {}
    for i in range(num_employees):
        for j in range(num_projects):
            x[i, j] = model.addVar(
                lb=0.0,
                ub=assignment_capacity[i][j],
                vtype=GRB.CONTINUOUS,
                name=f"x_{i}_{j}"
            )

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(assignment_cost[i][j] * x[i, j]
                    for i in range(num_employees)
                    for j in range(num_projects)),
        GRB.MINIMIZE
    )

    # Employee availability constraints: total hours assigned equals availability
    for i in range(num_employees):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_projects)) == employee_availability[i],
            name=f"availability_{i}"
        )

    # Project requirement constraints: total hours assigned meets requirement
    for j in range(num_projects):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_employees)) == project_requirement[j],
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