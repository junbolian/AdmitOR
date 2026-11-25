import gurobipy as gp
from gurobipy import GRB

def solve(params):
    individual_total_capacity = params["individual_total_capacity"]
    project_demand = params["project_demand"]
    assignment_cost = params["assignment_cost"]
    max_contribution_per_project = params["max_contribution_per_project"]

    num_persons = 8
    num_projects = 7
    persons = range(num_persons)
    projects = range(num_projects)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(persons, projects, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(assignment_cost[i][j] * x[i, j] for i in persons for j in projects),
        GRB.MINIMIZE
    )

    # Each individual must fully utilize their total capacity
    for i in persons:
        model.addConstr(
            gp.quicksum(x[i, j] for j in projects) == individual_total_capacity[i],
            name=f"capacity_{i}"
        )

    # Each project must meet its demand
    for j in projects:
        model.addConstr(
            gp.quicksum(x[i, j] for i in persons) == project_demand[j],
            name=f"demand_{j}"
        )

    # Max contribution per individual per project
    for i in persons:
        for j in projects:
            model.addConstr(
                x[i, j] <= max_contribution_per_project[i][j],
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
        return {"objective": None, "status": f"gurobi_status_{status}"}