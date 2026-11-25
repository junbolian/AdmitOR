import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    team_costs = params["team_costs"]
    requirement_thresholds = params["requirement_thresholds"]

    coverage_sets = [
        [1, 4, 5],
        [2, 7, 8, 9, 10],
        [1, 2, 4, 5],
        [2, 3, 5, 6, 8, 9],
        [1, 11],
        [5, 6, 7, 8],
        [2, 6, 9],
        [1, 2, 3, 8, 9],
        [1, 4, 7],
        [2, 3, 7, 10],
        [3, 4, 5, 7, 8],
        [1, 4, 5, 8, 9, 10],
        [1, 3, 5, 7, 8, 9, 10],
        [1, 3, 4, 5, 6, 8, 10, 11],
        [3, 8, 9, 11],
        [2, 5, 6, 11],
        [3, 8, 11],
        [3, 4, 6, 8, 9, 10],
        [1, 4, 5, 9],
        [1, 5, 6, 10],
    ]

    num_teams = len(team_costs)
    num_reqs = len(requirement_thresholds)

    teams = list(range(num_teams))
    reqs = list(range(num_reqs))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(teams, domain=pyo.Binary)

    model.cost = pyo.Objective(
        expr=sum(team_costs[t] * model.x[t] for t in teams),
        sense=pyo.minimize,
    )

    req_teams = {r: [t - 1 for t in coverage_sets[r]] for r in reqs}

    def coverage_rule(m, r):
        return sum(m.x[t] for t in req_teams[r]) >= requirement_thresholds[r]

    model.coverage = pyo.Constraint(reqs, rule=coverage_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}