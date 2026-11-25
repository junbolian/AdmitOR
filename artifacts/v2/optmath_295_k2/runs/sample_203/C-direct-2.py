import gurobipy as gp
from gurobipy import GRB

def solve(params):
    consultant_hours = params["consultant_hours"]  # list of length num_consultants
    project_hours = params["project_hours"]        # list of length num_projects
    capacity = params["capacity"]                  # 2D list [consultants][projects]
    cost = params["cost"]                          # 2D list [consultants][projects]

    num_consultants = len(consultant_hours)
    num_projects = len(project_hours)

    model = gp.Model("consulting_assignment")
    model.setParam("OutputFlag", 0)

    # Decision variables: hours consultant i works on project j
    x = {}
    for i in range(num_consultants):
        for j in range(num_projects):
            x[i, j] = model.addVar(
                lb=0.0,
                ub=capacity[i][j],
                vtype=GRB.CONTINUOUS,
                name=f"x_{i}_{j}"
            )

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(num_consultants) for j in range(num_projects)),
        GRB.MINIMIZE
    )

    # Consultant hour constraints: each consultant works exactly their required hours
    for i in range(num_consultants):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_projects)) == consultant_hours[i],
            name=f"consultant_{i}_hours"
        )

    # Project hour constraints: each project receives exactly its required hours
    for j in range(num_projects):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_consultants)) == project_hours[j],
            name=f"project_{j}_hours"
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