import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    team_cost = params["team_cost"]
    req_min_teams = params["req_min_teams"]

    teams = list(range(1, 12))

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

    model = pyo.ConcreteModel()
    model.TEAMS = pyo.Set(initialize=teams)
    model.COVERAGE = pyo.Set(initialize=range(20))

    model.x = pyo.Var(model.TEAMS, domain=pyo.Binary)

    model.deploy_cost = pyo.Objective(
        expr=sum(team_cost[t - 1] * model.x[t] for t in model.TEAMS),
        sense=pyo.minimize,
    )

    def coverage_rule(m, i):
        return sum(m.x[t] for t in coverage_sets[i]) >= req_min_teams[i]

    model.coverage_constraint = pyo.Constraint(model.COVERAGE, rule=coverage_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.deploy_cost))
    return {"objective": obj_val, "status": "optimal"}