import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    team_costs = params["team_costs"]
    area_requirements = params["area_requirements"]

    num_teams = len(team_costs)
    num_areas = len(area_requirements)

    # Coverage structure: teams covering each area (1-indexed as in problem)
    coverage = {
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
        17: [5, 7, 8],
    }

    model = pyo.ConcreteModel()
    model.teams = pyo.RangeSet(1, num_teams)
    model.areas = pyo.RangeSet(1, num_areas)

    model.x = pyo.Var(model.teams, domain=pyo.Binary)

    def obj_rule(m):
        return sum(team_costs[t - 1] * m.x[t] for t in m.teams)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def cover_rule(m, a):
        return sum(m.x[t] for t in coverage[a]) >= area_requirements[a - 1]
    model.cover = pyo.Constraint(model.areas, rule=cover_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}