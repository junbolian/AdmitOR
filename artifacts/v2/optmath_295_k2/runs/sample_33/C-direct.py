import gurobipy as gp
from gurobipy import GRB

def solve(params):
    employee_availability = params["employee_availability"]
    project_requirement = params["project_requirement"]
    assignment_cost = params["assignment_cost"]
    assignment_limit = params["assignment_limit"]

    num_employees = len(employee_availability)
    num_projects = len(project_requirement)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: hours assigned from employee i to project j
    x = {}
    for i in range(num_employees):
        for j in range(num_projects):
            x[i, j] = model.addVar(
                lb=0.0,
                ub=assignment_limit[i][j],
                vtype=GRB.CONTINUOUS,
                name=f"x_{i}_{j}"
            )

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(
            assignment_cost[i][j] * x[i, j]
            for i in range(num_employees)
            for j in range(num_projects)
        ),
        GRB.MINIMIZE
    )

    # Employee availability constraints
    for i in range(num_employees):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_projects)) <= employee_availability[i],
            name=f"avail_{i}"
        )

    # Project demand constraints
    for j in range(num_projects):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_employees)) >= project_requirement[j],
            name=f"demand_{j}"
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