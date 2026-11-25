import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    team_costs = params["team_costs"]

    teams = list(range(10))
    locations = list(range(17))

    coverage = {
        0: [0, 1, 3, 4, 5, 6, 8],
        1: [0, 2, 3, 4, 5, 8, 9],
        2: [0, 1, 2, 3, 7, 9],
        3: [1, 4, 7, 9],
        4: [0, 6],
        5: [0, 1, 2, 4, 7, 8, 9],
        6: [0, 1, 3, 4, 8],
        7: [2, 7, 8],
        8: [2, 3, 4, 6],
        9: [0, 1, 4, 5],
        10: [1, 2, 6, 8],
        11: [4, 6, 7, 8, 9],
        12: [1, 2, 7, 9],
        13: [0, 1, 2, 4, 5, 8, 9],
        14: [1, 5, 7, 8],
        15: [1, 2, 4, 6, 9],
        16: [0, 1, 2, 4, 7, 8, 9],
    }

    model = pyo.ConcreteModel()

    model.x = pyo.Var(teams, domain=pyo.Binary)

    def obj_rule(m):
        return sum(team_costs[t] * m.x[t] for t in teams)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def cover_rule(m, loc):
        return sum(m.x[t] for t in coverage[loc]) >= 1
    model.cover = pyo.Constraint(locations, rule=cover_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}