import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    team_costs_data = params["team_costs"]

    teams = list(range(1, 11))
    locations = list(range(1, 18))

    team_costs = {t: team_costs_data[t - 1] for t in teams}

    coverage = {
        1: [1, 2, 4, 5, 6, 7, 9],
        2: [1, 3, 4, 5, 6, 9, 10],
        3: [1, 2, 3, 4, 8, 10],
        4: [2, 5, 8, 10],
        5: [1, 7],
        6: [1, 2, 3, 5, 8, 9, 10],
        7: [1, 2, 4, 5, 9],
        8: [3, 8, 9],
        9: [3, 4, 5, 7],
        10: [1, 2, 5, 6],
        11: [2, 3, 7, 9],
        12: [5, 7, 8, 9, 10],
        13: [2, 3, 8, 10],
        14: [1, 2, 3, 5, 6, 9, 10],
        15: [2, 6, 8, 9],
        16: [2, 3, 5, 7, 10],
        17: [1, 2, 3, 5, 8, 9, 10],
    }

    model = pyo.ConcreteModel()

    model.TEAMS = pyo.Set(initialize=teams)
    model.LOCS = pyo.Set(initialize=locations)

    model.x = pyo.Var(model.TEAMS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(team_costs[t] * m.x[t] for t in m.TEAMS)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def cover_rule(m, j):
        return sum(m.x[t] for t in coverage[j]) >= 1

    model.cover_con = pyo.Constraint(model.LOCS, rule=cover_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}