import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    costs = params["team_costs"]
    n_teams = 13
    n_zones = 18

    coverage = {
        1: [3, 4, 6, 7, 9, 10],
        2: [1, 2, 3, 7, 11],
        3: [1, 5, 8, 9, 12, 13],
        4: [1, 3, 4, 5, 6, 7, 8, 9, 10, 13],
        5: [1, 2, 8, 9, 10, 11, 12, 13],
        6: [1, 7, 10, 13],
        7: [4, 5, 7, 8, 9, 11, 13],
        8: [2, 3, 6, 8],
        9: [1, 2, 3, 6, 7, 8, 9, 10, 12, 13],
        10: [1, 2, 3, 7, 8, 10, 11, 12, 13],
        11: [1, 2, 4, 5, 7, 8, 9, 10, 12],
        12: [1, 8, 9, 11, 12, 13],
        13: [2, 3, 4, 5, 6, 7, 10, 13],
        14: [1, 2, 5, 8, 9, 11],
        15: [4, 6, 8, 13],
        16: [1, 2, 3, 4, 6, 8, 10],
        17: [2, 11],
        18: [1, 2, 5, 10, 11, 12],
    }

    teams = list(range(1, n_teams + 1))
    zones = list(range(1, n_zones + 1))

    model = pyo.ConcreteModel()
    model.x = pyo.Var(teams, domain=pyo.Binary)
    model.obj = pyo.Objective(
        expr=sum(costs[i - 1] * model.x[i] for i in teams),
        sense=pyo.minimize,
    )

    def cover_rule(mdl, j):
        return sum(mdl.x[i] for i in coverage[j]) >= 1

    model.cover = pyo.Constraint(zones, rule=cover_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}