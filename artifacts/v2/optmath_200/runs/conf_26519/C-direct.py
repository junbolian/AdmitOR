import gurobipy as gp
from gurobipy import GRB

def solve(params):
    employee_capacity = params["employee_capacity"]
    project_demand = params["project_demand"]
    allocation_limit = params["allocation_limit"]
    cost_per_hour = params["cost_per_hour"]

    num_employees = len(employee_capacity)
    num_projects = len(project_demand)

    model = gp.Model("workforce_allocation")
    model.setParam("OutputFlag", 0)

    # Decision variables: hours employee i contributes to project j
    x = {}
    for i in range(num_employees):
        for j in range(num_projects):
            x[i, j] = model.addVar(
                lb=0.0,
                ub=allocation_limit[i][j],
                vtype=GRB.CONTINUOUS,
                name=f"x_{i}_{j}"
            )

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost_per_hour[i][j] * x[i, j]
                    for i in range(num_employees)
                    for j in range(num_projects)),
        GRB.MINIMIZE
    )

    # Constraint 1: Each employee's total hours <= their capacity
    for i in range(num_employees):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_projects)) <= employee_capacity[i],
            name=f"capacity_{i}"
        )

    # Constraint 2: Each project's demand is exactly met
    for j in range(num_projects):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_employees)) == project_demand[j],
            name=f"demand_{j}"
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