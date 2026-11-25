import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    team_cost = params["team_cost"]
    area_requirement = params["area_requirement"]

    teams = list(range(1, 14))
    areas = list(range(1, 18))

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

    model.TEAMS = pyo.Set(initialize=teams)
    model.AREAS = pyo.Set(initialize=areas)

    model.x = pyo.Var(model.TEAMS, domain=pyo.Binary)

    model.cost = pyo.Objective(
        expr=sum(team_cost[t - 1] * model.x[t] for t in model.TEAMS),
        sense=pyo.minimize,
    )

    def area_rule(mdl, a):
        return sum(mdl.x[t] for t in coverage[a]) >= area_requirement[a - 1]

    model.area_constraints = pyo.Constraint(model.AREAS, rule=area_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.cost))
    except Exception as exc:
        return {"objective": None, "status": "failed: " + str(exc)}

    return {"objective": obj_val, "status": "optimal"}