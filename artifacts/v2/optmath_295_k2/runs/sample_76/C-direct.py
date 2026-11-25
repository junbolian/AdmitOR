import gurobipy as gp
from gurobipy import GRB

def solve(params):
    team_costs = params["team_costs"]
    task_requirements = params["task_requirements"]

    num_teams = 15
    num_tasks = 16

    # Coverage matrix: task_coverage[j][i] = 1 if team i+1 can cover task j+1
    task_coverage = [
        [0,0,0,1,1,0,1,1,0,1,0,1,1,1,0],  # Task 1: teams 4,5,7,8,10,12,13,14
        [0,1,1,0,0,0,1,0,1,1,0,0,1,1,0],  # Task 2: teams 2,3,7,9,10,13,14
        [0,0,1,0,1,1,1,0,0,0,1,1,0,0,0],  # Task 3: teams 3,5,6,7,11,12
        [1,1,0,1,0,1,0,1,1,1,0,0,1,0,0],  # Task 4: teams 1,2,4,6,8,9,10,13
        [0,1,0,1,0,1,1,1,0,1,0,0,1,0,1],  # Task 5: teams 2,4,6,7,8,10,13,15
        [0,0,1,0,0,0,1,1,0,1,1,0,0,0,1],  # Task 6: teams 3,7,8,10,11,15
        [1,0,1,0,0,0,0,0,1,1,0,1,0,1,0],  # Task 7: teams 1,3,9,10,12,14
        [0,0,0,0,1,1,0,1,0,0,0,0,0,1,1],  # Task 8: teams 5,6,8,14,15
        [1,1,0,0,0,0,0,0,1,1,0,0,0,1,0],  # Task 9: teams 1,2,9,10,14
        [0,0,1,0,0,0,1,0,0,0,1,1,1,0,0],  # Task 10: teams 3,7,11,12,13
        [1,0,0,1,0,0,0,1,0,0,1,1,1,1,1],  # Task 11: teams 1,4,8,11,12,13,14,15
        [0,1,0,0,1,0,0,0,0,0,0,0,0,0,1],  # Task 12: teams 2,5,15
        [0,1,0,1,0,0,0,0,1,0,1,0,1,0,1],  # Task 13: teams 2,4,9,11,13,15
        [0,0,1,0,0,0,0,1,1,0,1,1,0,0,1],  # Task 14: teams 3,8,9,11,12,15
        [0,0,1,0,0,1,1,0,1,0,0,1,0,0,1],  # Task 15: teams 3,6,7,9,12,15
        [0,0,0,0,0,0,0,0,0,1,0,0,1,0,1],  # Task 16: teams 10,13,15
    ]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_teams, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(team_costs[i] * x[i] for i in range(num_teams)),
        GRB.MINIMIZE
    )

    for j in range(num_tasks):
        model.addConstr(
            gp.quicksum(task_coverage[j][i] * x[i] for i in range(num_teams)) >= task_requirements[j],
            name=f"task_{j}"
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