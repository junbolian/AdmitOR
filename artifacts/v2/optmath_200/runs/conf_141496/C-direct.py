import gurobipy as gp
from gurobipy import GRB

def solve(params):
    workloads = [
        params["project_workload_0"],
        params["project_workload_1"],
        params["project_workload_2"],
        params["project_workload_3"],
        params["project_workload_4"],
        params["project_workload_5"],
        params["project_workload_6"],
    ]
    team_capacity = params["team_capacity"]
    num_teams = int(params["num_teams"])
    num_projects = int(params["num_projects"])

    projects = range(num_projects)
    teams = range(num_teams)

    model = gp.Model("project_assignment")
    model.setParam("OutputFlag", 0)

    # x[j, t] = 1 if project j is assigned to team t
    x = model.addVars(num_projects, num_teams, vtype=GRB.BINARY, name="x")
    # y[t] = 1 if team t is active
    y = model.addVars(num_teams, vtype=GRB.BINARY, name="y")

    # Objective: minimize number of active teams
    model.setObjective(gp.quicksum(y[t] for t in teams), GRB.MINIMIZE)

    # Each project assigned to exactly one team
    for j in projects:
        model.addConstr(gp.quicksum(x[j, t] for t in teams) == 1, name=f"assign_{j}")

    # Team capacity constraints
    for t in teams:
        model.addConstr(
            gp.quicksum(workloads[j] * x[j, t] for j in projects) <= team_capacity * y[t],
            name=f"capacity_{t}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}