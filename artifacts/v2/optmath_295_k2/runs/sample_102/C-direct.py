import gurobipy as gp
from gurobipy import GRB


def solve(params):
    employee_availability = params["employee_availability"]
    project_requirements = params["project_requirements"]
    assignment_costs = params["assignment_costs"]
    assignment_limits = params["assignment_limits"]

    n_employees = len(employee_availability)
    n_projects = len(project_requirements)

    model = gp.Model("workforce_allocation")
    model.setParam("OutputFlag", 0)

    # Decision variables: hours assigned from person i to project j
    x = {}
    for i in range(n_employees):
        for j in range(n_projects):
            x[i, j] = model.addVar(
                lb=0.0,
                ub=assignment_limits[i][j],
                vtype=GRB.CONTINUOUS,
                name=f"x_{i}_{j}",
            )

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(
            assignment_costs[i][j] * x[i, j]
            for i in range(n_employees)
            for j in range(n_projects)
        ),
        GRB.MINIMIZE,
    )

    # Employee availability constraints
    for i in range(n_employees):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_projects)) <= employee_availability[i],
            name=f"avail_{i}",
        )

    # Project requirement constraints (exactly met)
    for j in range(n_projects):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_employees)) == project_requirements[j],
            name=f"req_{j}",
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
        return {"objective": None, "status": f"gurobi_status_{status}"}