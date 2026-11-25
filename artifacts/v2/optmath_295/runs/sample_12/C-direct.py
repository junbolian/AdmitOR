import gurobipy as gp
from gurobipy import GRB


def solve(params):
    employee_availability = params["employee_availability"]
    project_requirements = params["project_requirements"]
    assignment_cost = params["assignment_cost"]
    assignment_capacity = params["assignment_capacity"]

    num_employees = len(employee_availability)
    num_projects = len(project_requirements)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: hours employee i works on project j
    x = {}
    for i in range(num_employees):
        for j in range(num_projects):
            x[i, j] = model.addVar(
                lb=0.0,
                ub=assignment_capacity[i][j],
                vtype=GRB.CONTINUOUS,
                name=f"x_{i}_{j}"
            )

    # Objective: minimize total assignment cost
    model.setObjective(
        gp.quicksum(assignment_cost[i][j] * x[i, j]
                    for i in range(num_employees)
                    for j in range(num_projects)),
        GRB.MINIMIZE
    )

    # Employee availability constraints
    for i in range(num_employees):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_projects)) <= employee_availability[i],
            name=f"avail_{i}"
        )

    # Project requirement constraints (exact)
    for j in range(num_projects):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_employees)) == project_requirements[j],
            name=f"req_{j}"
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