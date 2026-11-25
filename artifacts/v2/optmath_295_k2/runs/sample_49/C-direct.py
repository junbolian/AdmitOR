import gurobipy as gp
from gurobipy import GRB

def solve(params):
    team_costs = params["team_costs"]
    location_requirements = params["location_requirements"]

    # Coverage sets: which teams can cover each location (0-indexed internally)
    coverage_sets = {
        0:  [2, 5, 6, 7, 8, 9, 11, 14],
        1:  [2, 5, 7, 13],
        2:  [1, 2, 4, 5, 6, 9, 10, 12, 13],
        3:  [3, 6, 13, 14],
        4:  [2, 6, 10],
        5:  [4, 6, 8, 14],
        6:  [1, 4, 5, 8, 10, 11, 12, 13, 14],
        7:  [1, 5, 11, 14],
        8:  [1, 2, 3, 6, 7, 10, 11, 12],
        9:  [6, 11, 12, 13],
        10: [1, 3, 4, 6, 7, 9],
        11: [1, 3, 5, 8, 9],
        12: [1, 4, 9, 11, 12, 13, 14],
        13: [2, 4, 7, 8, 13],
        14: [5, 7, 8, 9],
        15: [1, 5, 6, 8, 11, 13],
        16: [1, 4, 5, 6, 8, 14],
        17: [3, 8, 10, 11, 12, 14],
        18: [2, 5, 7, 12, 13],
        19: [1, 3, 4, 5, 10, 11, 13],
        20: [1, 8, 12, 14],
    }

    num_teams = 14
    num_locations = 21
    teams = range(1, num_teams + 1)
    locations = range(num_locations)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: 1 if team t is selected
    x = model.addVars(teams, vtype=GRB.BINARY, name="x")

    # Objective: minimize total deployment cost
    model.setObjective(
        gp.quicksum(team_costs[t - 1] * x[t] for t in teams),
        GRB.MINIMIZE
    )

    # Coverage constraints
    for loc in locations:
        required = location_requirements[loc]
        eligible = coverage_sets[loc]
        model.addConstr(
            gp.quicksum(x[t] for t in eligible) >= required,
            name=f"cov_{loc}"
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