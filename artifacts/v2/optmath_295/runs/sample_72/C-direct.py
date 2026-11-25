import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]
    employee_capacity = params["employee_capacity"]
    project_demand = params["project_demand"]
    per_project_limit = params["per_project_limit"]

    num_employees = 5
    num_projects = 5

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_employees, num_projects, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(num_employees) for j in range(num_projects)),
        GRB.MINIMIZE
    )

    for i in range(num_employees):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_projects)) == employee_capacity[i],
            name=f"emp_cap_{i}"
        )

    for j in range(num_projects):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_employees)) == project_demand[j],
            name=f"proj_demand_{j}"
        )

    for i in range(num_employees):
        for j in range(num_projects):
            model.addConstr(x[i, j] <= per_project_limit[i][j], name=f"limit_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}