import gurobipy as gp
from gurobipy import GRB


def solve(params):
    availability = params["availability"]
    requirements = params["requirements"]
    cost = params["cost"]
    limit = params["limit"]

    num_persons = len(availability)
    num_projects = len(requirements)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: hours person i works on project j
    x = {}
    for i in range(num_persons):
        for j in range(num_projects):
            x[i, j] = model.addVar(
                lb=0.0,
                ub=limit[i][j],
                vtype=GRB.CONTINUOUS,
                name=f"x_{i}_{j}"
            )

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(num_persons) for j in range(num_projects)),
        GRB.MINIMIZE
    )

    # Availability constraints: each person's total hours <= their availability
    for i in range(num_persons):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_projects)) <= availability[i],
            name=f"avail_{i}"
        )

    # Requirement constraints: each project must receive exactly its required hours
    for j in range(num_projects):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_persons)) == requirements[j],
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
        return {"objective": None, "status": f"status_{model.Status}"}