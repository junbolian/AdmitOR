import gurobipy as gp
from gurobipy import GRB

def solve(params):
    team_costs = params["team_costs"]
    task_requirements = params["task_requirements"]

    num_teams = 15
    num_tasks = 16

    # Coverage matrix: coverage[j][i] = 1 if team i+1 can cover task j+1
    coverage = [
        [0,0,0,1,1,0,1,1,0,1,0,1,1,1,0],  # Task 1
        [0,1,1,0,0,0,1,0,1,1,0,0,1,1,0],  # Task 2
        [0,0,1,0,1,1,1,0,0,0,1,1,0,0,0],  # Task 3
        [1,1,0,1,0,1,0,1,1,1,0,0,1,0,0],  # Task 4
        [0,1,0,1,0,1,1,1,0,1,0,0,1,0,1],  # Task 5
        [0,0,1,0,0,0,1,1,0,1,1,0,0,0,1],  # Task 6
        [1,0,1,0,0,0,0,0,1,1,0,1,0,1,0],  # Task 7
        [0,0,0,0,1,1,0,1,0,0,0,0,0,1,1],  # Task 8
        [1,1,0,0,0,0,0,0,1,1,0,0,0,1,0],  # Task 9
        [0,0,1,0,0,0,1,0,0,0,1,1,1,0,0],  # Task 10
        [1,0,0,1,0,0,0,1,0,0,1,1,1,1,1],  # Task 11
        [0,1,0,0,1,0,0,0,0,0,0,0,0,0,1],  # Task 12
        [0,1,0,1,0,0,0,0,1,0,1,0,1,0,1],  # Task 13
        [0,0,1,0,0,0,0,1,1,0,1,1,0,0,1],  # Task 14
        [0,0,1,0,0,1,1,0,1,0,0,1,0,0,1],  # Task 15
        [0,0,0,0,0,0,0,0,0,1,0,0,1,0,1],  # Task 16
    ]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary decision variables: select team i or not
    x = model.addVars(num_teams, vtype=GRB.BINARY, name="x")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(team_costs[i] * x[i] for i in range(num_teams)),
        GRB.MINIMIZE
    )

    # Coverage constraints
    for j in range(num_tasks):
        model.addConstr(
            gp.quicksum(coverage[j][i] * x[i] for i in range(num_teams)) >= task_requirements[j],
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
        return {"objective": None, "status": f"solver_status_{model.Status}"}