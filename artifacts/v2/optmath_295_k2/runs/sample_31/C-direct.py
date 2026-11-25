import gurobipy as gp
from gurobipy import GRB


def solve(params):
    employee_supply = params["employee_supply"]
    project_demand = params["project_demand"]
    cost = params["cost"]
    assignment_capacity = params["assignment_capacity"]

    num_employees = len(employee_supply)
    num_projects = len(project_demand)

    model = gp.Model("employee_project_assignment")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(num_employees):
        for j in range(num_projects):
            x[i, j] = model.addVar(
                lb=0.0,
                ub=assignment_capacity[i][j],
                obj=cost[i][j],
                name=f"x_{i}_{j}",
            )

    for i in range(num_employees):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_projects)) == employee_supply[i],
            name=f"supply_{i}",
        )

    for j in range(num_projects):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_employees)) == project_demand[j],
            name=f"demand_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": f"infeasible_or_failed (gurobi_status={model.status})"}