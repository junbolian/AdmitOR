import gurobipy as gp
from gurobipy import GRB

def solve(params):
    team_costs = params["team_costs"]
    area_requirements = params["area_requirements"]
    
    # Coverage structure: which teams can cover each area
    area_coverage = {
        1: [5, 7, 11],
        2: [1, 2, 5, 9, 11],
        3: [4, 6],
        4: [2, 5, 8, 10, 11],
        5: [2, 6, 7, 9, 10],
        6: [1, 7, 8, 12],
        7: [3, 5, 13],
        8: [2, 7, 9, 12, 13],
        9: [13],
        10: [2, 5, 6, 7, 9, 12],
        11: [2, 3, 6, 7, 8, 10, 11],
        12: [6, 11],
        13: [2, 3, 12],
        14: [6, 10, 11, 12],
        15: [4, 5, 9, 11],
        16: [3, 5, 9, 12, 13],
        17: [5, 7, 8]
    }
    
    num_teams = 13
    num_areas = 17
    
    model = gp.Model("emergency_response_team_selection")
    model.Params.LogToConsole = 0
    
    # Decision variables: x[t] = 1 if team t is selected, 0 otherwise
    x = model.addVars(range(1, num_teams + 1), vtype=GRB.BINARY, name="x")
    
    # Objective: minimize total deployment cost
    model.setObjective(
        gp.quicksum(team_costs[t - 1] * x[t] for t in range(1, num_teams + 1)),
        GRB.MINIMIZE
    )
    
    # Constraints: each area must be covered by at least the required number of teams
    for area in range(1, num_areas + 1):
        covering_teams = area_coverage[area]
        model.addConstr(
            gp.quicksum(x[t] for t in covering_teams) >= area_requirements[area - 1],
            name=f"area_{area}_coverage"
        )
    
    model.optimize()
    
    if model.status == GRB.OPTIMAL:
        return {
            "objective": model.objVal,
            "status": "optimal"
        }
    elif model.status == GRB.INFEASIBLE:
        return {
            "objective": None,
            "status": "infeasible"
        }
    else:
        return {
            "objective": None,
            "status": f"status_{model.status}"
        }