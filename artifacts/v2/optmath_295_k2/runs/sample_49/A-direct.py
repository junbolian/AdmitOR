import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    team_costs = params["team_costs"]
    location_requirements = params["location_requirements"]

    coverage = {
        1: [2, 5, 6, 7, 8, 9, 11, 14],
        2: [2, 5, 7, 13],
        3: [1, 2, 4, 5, 6, 9, 10, 12, 13],
        4: [3, 6, 13, 14],
        5: [2, 6, 10],
        6: [4, 6, 8, 14],
        7: [1, 4, 5, 8, 10, 11, 12, 13, 14],
        8: [1, 5, 11, 14],
        9: [1, 2, 3, 6, 7, 10, 11, 12],
        10: [6, 11, 12, 13],
        11: [1, 3, 4, 6, 7, 9],
        12: [1, 3, 5, 8, 9],
        13: [1, 4, 9, 11, 12, 13, 14],
        14: [2, 4, 7, 8, 13],
        15: [5, 7, 8, 9],
        16: [1, 5, 6, 8, 11, 13],
        17: [1, 4, 5, 6, 8, 14],
        18: [3, 8, 10, 11, 12, 14],
        19: [2, 5, 7, 12, 13],
        20: [1, 3, 4, 5, 10, 11, 13],
        21: [1, 8, 12, 14],
    }

    model = pyo.ConcreteModel()

    model.TEAMS = pyo.RangeSet(1, len(team_costs))
    model.LOCATIONS = pyo.RangeSet(1, len(location_requirements))

    model.x = pyo.Var(model.TEAMS, domain=pyo.Binary)

    def cost_rule(mdl):
        return sum(team_costs[i - 1] * mdl.x[i] for i in mdl.TEAMS)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def cover_rule(mdl, j):
        teams_for_location = coverage[j]
        return sum(mdl.x[i] for i in teams_for_location) >= location_requirements[j - 1]

    model.coverage_con = pyo.Constraint(model.LOCATIONS, rule=cover_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}