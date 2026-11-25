import gurobipy as gp
from gurobipy import GRB

def solve(params):
    member_capacity = params["member_capacity"]  # list of 6 values
    project_requirement = params["project_requirement"]  # list of 8 values

    num_members = 6
    num_projects = 8

    # Cost matrix [person][project]
    cost = [
        [25, 32, 15, 28, 20, 18, 30, 22],
        [19, 27, 23, 31, 17, 25, 21, 29],
        [33, 18, 26, 14, 28, 22, 16, 24],
        [21, 29, 17, 25, 32, 19, 27, 15],
        [28, 22, 30, 18, 23, 31, 25, 17],
        [16, 24, 20, 28, 15, 27, 23, 31],
    ]

    # Per-member per-project capacity limit [person][project]
    limit = [
        [10,  7,  5,  9,  8,  6, 10,  7],
        [ 8,  9,  7,  6, 10,  8,  7,  9],
        [ 7,  8, 10,  8,  6,  9,  8,  6],
        [ 9,  6,  8, 10,  7,  7,  9,  8],
        [ 6, 10,  9,  7,  9,  6,  8, 10],
        [ 8,  7,  6,  9,  8, 10,  7,  7],
    ]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = time person i spends on project j
    x = [[
        model.addVar(lb=0.0, ub=limit[i][j], name=f"x_{i}_{j}")
        for j in range(num_projects)]
        for i in range(num_members)]

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i][j]
                    for i in range(num_members)
                    for j in range(num_projects)),
        GRB.MINIMIZE
    )

    # Each team member's total time equals their capacity
    for i in range(num_members):
        model.addConstr(
            gp.quicksum(x[i][j] for j in range(num_projects)) == member_capacity[i],
            name=f"member_cap_{i}"
        )

    # Each project's total effort equals its requirement
    for j in range(num_projects):
        model.addConstr(
            gp.quicksum(x[i][j] for i in range(num_members)) == project_requirement[j],
            name=f"proj_req_{j}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}