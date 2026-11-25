import gurobipy as gp
from gurobipy import GRB

def solve(params):
    employee_hours = params["employee_hours"]
    project_hours = params["project_hours"]
    cost = params["cost"]
    capacity = params["capacity"]

    num_employees = 6
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
            gp.quicksum(x[i, j] for j in range(num_projects)) == employee_hours[i],
            name=f"emp_{i}"
        )

    for j in range(num_projects):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_employees)) == project_hours[j],
            name=f"proj_{j}"
        )

    for i in range(num_employees):
        for j in range(num_projects):
            model.addConstr(x[i, j] <= capacity[i][j], name=f"cap_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}