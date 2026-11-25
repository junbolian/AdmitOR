import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    deployment_costs = params["deployment_costs"]
    coverage_requirements = params["coverage_requirements"]

    teams = list(range(1, 13))
    locations = list(range(1, 19))

    eligible_teams = {
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

    cost = {t: deployment_costs[t - 1] for t in teams}
    required = {loc: coverage_requirements[loc - 1] for loc in locations}

    model = pyo.ConcreteModel()

    model.TEAMS = pyo.Set(initialize=teams)
    model.LOCATIONS = pyo.Set(initialize=locations)

    model.x = pyo.Var(model.TEAMS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[t] * m.x[t] for t in m.TEAMS)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def coverage_rule(m, loc):
        return sum(m.x[t] for t in eligible_teams[loc]) >= required[loc]

    model.coverage = pyo.Constraint(model.LOCATIONS, rule=coverage_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}