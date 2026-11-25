import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    team_costs = params["team_costs"]
    area_requirements = params["area_requirements"]

    num_teams = 13
    num_areas = 17

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

    model.TEAMS = pyo.RangeSet(1, num_teams)
    model.AREAS = pyo.RangeSet(1, num_areas)

    model.x = pyo.Var(model.TEAMS, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(team_costs[i - 1] * model.x[i] for i in model.TEAMS),
        sense=pyo.minimize,
    )

    model.coverage_constraints = pyo.Constraint(model.AREAS)

    for a in model.AREAS:
        teams = coverage[a]
        model.coverage_constraints[a] = pyo.Constraint(
            expr=sum(model.x[t] for t in teams) >= area_requirements[a - 1]
        )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}