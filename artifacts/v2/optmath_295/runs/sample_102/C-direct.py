import gurobipy as gp
from gurobipy import GRB

def solve(params):
    employee_capacity = params["employee_capacity"]
    project_demand = params["project_demand"]
    cost_matrix = params["cost_matrix"]
    assignment_limit = params["assignment_limit"]

    num_employees = len(employee_capacity)
    num_projects = len(project_demand)

    model = gp.Model("workforce_allocation")
    model.setParam("OutputFlag", 0)

    # Decision variables: hours employee i assigns to project j
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
        gp.quicksum(cost_matrix[i][j] * x[i, j]
                    for i in range(num_employees)
                    for j in range(num_projects)),
        GRB.MINIMIZE
    )

    # Employee capacity constraints
    for i in range(num_employees):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_projects)) <= employee_capacity[i],
            name=f"capacity_{i}"
        )

    # Project demand constraints (exactly met)
    for j in range(num_projects):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_employees)) == project_demand[j],
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