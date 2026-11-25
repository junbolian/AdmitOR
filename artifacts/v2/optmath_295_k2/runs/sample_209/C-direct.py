import gurobipy as gp
from gurobipy import GRB

def solve(params):
    person_availability = params["person_availability"]
    project_requirement = params["project_requirement"]
    assignment_cost = params["assignment_cost"]
    assignment_upper_limit = params["assignment_upper_limit"]

    n_persons = 7
    n_projects = 7
    persons = range(n_persons)
    projects = range(n_projects)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(persons, projects, lb=0.0, name="x")

    # Objective: minimize total assignment cost
    model.setObjective(
        gp.quicksum(assignment_cost[i][j] * x[i, j] for i in persons for j in projects),
        GRB.MINIMIZE
    )

    # Person availability constraints
    for i in persons:
        model.addConstr(
            gp.quicksum(x[i, j] for j in projects) <= person_availability[i],
            name=f"avail_{i}"
        )

    # Project requirement constraints (exact)
    for j in projects:
        model.addConstr(
            gp.quicksum(x[i, j] for i in persons) == project_requirement[j],
            name=f"req_{j}"
        )

    # Per-assignment upper limits
    for i in persons:
        for j in projects:
            model.addConstr(
                x[i, j] <= assignment_upper_limit[i][j],
                name=f"limit_{i}_{j}"
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