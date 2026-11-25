import gurobipy as gp
from gurobipy import GRB


def solve(params):
    employee_supply = params["employee_supply"]
    project_demand = params["project_demand"]
    cost = params["cost"]
    assignment_capacity = params["assignment_capacity"]

    num_employees = len(employee_supply)
    num_projects = len(project_demand)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_employees, num_projects, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(num_employees) for j in range(num_projects)),
        GRB.MINIMIZE
    )

    for i in range(num_employees):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_projects)) == employee_supply[i],
            name=f"supply_{i}"
        )

    for j in range(num_projects):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_employees)) == project_demand[j],
            name=f"demand_{j}"
        )

    for i in range(num_employees):
        for j in range(num_projects):
            model.addConstr(x[i, j] <= assignment_capacity[i][j], name=f"cap_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}