import gurobipy as gp
from gurobipy import GRB

def solve(params):
    individual_total_capacity = params["individual_total_capacity"]
    project_demand = params["project_demand"]
    assignment_cost = params["assignment_cost"]
    max_contribution_per_project = params["max_contribution_per_project"]

    num_persons = 8
    num_projects = 7

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = units assigned from person i to project j
    x = [[
        model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")
        for j in range(num_projects)
    ] for i in range(num_persons)]

    # Objective: minimize total assignment cost
    model.setObjective(
        gp.quicksum(
            assignment_cost[i][j] * x[i][j]
            for i in range(num_persons)
            for j in range(num_projects)
        ),
        GRB.MINIMIZE
    )

    # Each individual's total allocation must equal their total capacity
    for i in range(num_persons):
        model.addConstr(
            gp.quicksum(x[i][j] for j in range(num_projects)) == individual_total_capacity[i],
            name=f"capacity_{i}"
        )

    # Each project's demand must be met
    for j in range(num_projects):
        model.addConstr(
            gp.quicksum(x[i][j] for i in range(num_persons)) == project_demand[j],
            name=f"demand_{j}"
        )

    # Max contribution per individual per project
    for i in range(num_persons):
        for j in range(num_projects):
            model.addConstr(
                x[i][j] <= max_contribution_per_project[i][j],
                name=f"maxcontrib_{i}_{j}"
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