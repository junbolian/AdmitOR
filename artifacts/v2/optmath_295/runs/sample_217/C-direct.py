import gurobipy as gp
from gurobipy import GRB


def solve(params):
    team_cost = params["team_cost"]
    req_min_teams = params["req_min_teams"]

    n_teams = 11
    n_reqs = 20

    # Structural coverage sets (1-based team indices) for each of the 20 requirements.
    coverage_sets = [
        {1, 4, 5},
        {2, 7, 8, 9, 10},
        {1, 2, 4, 5},
        {2, 3, 5, 6, 8, 9},
        {1, 11},
        {5, 6, 7, 8},
        {2, 6, 9},
        {1, 2, 3, 8, 9},
        {1, 4, 7},
        {2, 3, 7, 10},
        {3, 4, 5, 7, 8},
        {1, 4, 5, 8, 9, 10},
        {1, 3, 5, 7, 8, 9, 10},
        {1, 3, 4, 5, 6, 8, 10, 11},
        {3, 8, 9, 11},
        {2, 5, 6, 11},
        {3, 8, 11},
        {3, 4, 6, 8, 9, 10},
        {1, 4, 5, 9},
        {1, 5, 6, 10},
    ]

    if len(team_cost) != n_teams:
        raise ValueError(f"team_cost must have length {n_teams}")
    if len(req_min_teams) != n_reqs:
        raise ValueError(f"req_min_teams must have length {n_reqs}")

    model = gp.Model("team_deployment")
    model.Params.OutputFlag = 0

    x = model.addVars(range(1, n_teams + 1), vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(team_cost[i - 1] * x[i] for i in range(1, n_teams + 1)),
        GRB.MINIMIZE,
    )

    for j in range(n_reqs):
        team_set = coverage_sets[j]
        rhs = req_min_teams[j]
        model.addConstr(
            gp.quicksum(x[i] for i in team_set) >= rhs,
            name=f"coverage_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"status_{model.status}"}