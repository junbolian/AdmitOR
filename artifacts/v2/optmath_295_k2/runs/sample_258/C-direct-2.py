import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity_person = params["capacity_person"]
    demand_project = params["demand_project"]
    cost_assign = params["cost_assign"]
    max_person_project = params["max_person_project"]

    num_persons = len(capacity_person)
    num_projects = len(demand_project)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: hours person i contributes to project j
    x = model.addVars(num_persons, num_projects, lb=0.0, name="x")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost_assign[i][j] * x[i, j] for i in range(num_persons) for j in range(num_projects)),
        GRB.MINIMIZE
    )

    # Constraint: each person's total hours <= their capacity
    for i in range(num_persons):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_projects)) <= capacity_person[i],
            name=f"cap_person_{i}"
        )

    # Constraint: each project's demand is fully met
    for j in range(num_projects):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_persons)) >= demand_project[j],
            name=f"demand_project_{j}"
        )

    # Constraint: per-person per-project max hours
    for i in range(num_persons):
        for j in range(num_projects):
            model.addConstr(
                x[i, j] <= max_person_project[i][j],
                name=f"max_pp_{i}_{j}"
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