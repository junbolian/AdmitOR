import gurobipy as gp
from gurobipy import GRB

def solve(params):
    consultant_availability = params["consultant_availability"]
    project_requirement = params["project_requirement"]
    assignment_cost = params["assignment_cost"]
    assignment_limit = params["assignment_limit"]

    num_consultants = len(consultant_availability)
    num_projects = len(project_requirement)

    model = gp.Model("project_assignment")
    model.setParam("OutputFlag", 0)

    # Decision variables: hours consultant i works on project j
    x = {}
    for i in range(num_consultants):
        for j in range(num_projects):
            x[i, j] = model.addVar(
                lb=0.0,
                ub=assignment_limit[i][j],
                vtype=GRB.CONTINUOUS,
                name=f"x_{i}_{j}"
            )

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(assignment_cost[i][j] * x[i, j]
                    for i in range(num_consultants)
                    for j in range(num_projects)),
        GRB.MINIMIZE
    )

    # Consultant availability constraints
    for i in range(num_consultants):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_projects)) <= consultant_availability[i],
            name=f"avail_{i}"
        )

    # Project requirement constraints (exactly)
    for j in range(num_projects):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_consultants)) == project_requirement[j],
            name=f"req_{j}"
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