import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    req = params["req"]

    teams = list(range(1, 13))
    locations = list(range(1, 19))

    coverage = {
        1: [4, 8, 10, 11],
        2: [2, 3, 7, 8, 10],
        3: [1, 4, 6],
        4: [8, 10, 12],
        5: [1, 3, 4, 8, 11],
        6: [1, 2, 6, 7, 8, 12],
        7: [1, 2, 4, 6, 9, 11],
        8: [2, 7, 8, 11],
        9: [2, 3, 4, 6],
        10: [2, 3, 5, 6, 9, 10, 11, 12],
        11: [2, 3, 4, 10],
        12: [4, 5, 9, 10, 11],
        13: [7, 9, 12],
        14: [1, 7, 9, 11],
        15: [6, 7, 8, 9, 10],
        16: [1, 4, 6, 7, 9, 10, 12],
        17: [4, 5, 7, 8, 10, 12],
        18: [1, 5, 8, 9],
    }

    model = pyo.ConcreteModel()
    model.TEAMS = pyo.Set(initialize=teams)
    model.LOCS = pyo.Set(initialize=locations)

    model.x = pyo.Var(model.TEAMS, within=pyo.Binary)

    def cover_rule(mdl, loc):
        return sum(mdl.x[t] for t in coverage[loc]) >= req[loc - 1]

    model.cover = pyo.Constraint(model.LOCS, rule=cover_rule)

    model.obj = pyo.Objective(
        expr=sum(cost[t - 1] * model.x[t] for t in model.TEAMS),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}