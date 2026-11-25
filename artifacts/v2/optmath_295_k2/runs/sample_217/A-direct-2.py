import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    team_costs = params["team_costs"]
    thresholds = params["requirement_thresholds"]

    n_teams = 11
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
    n_req = len(coverage_sets)

    model = pyo.ConcreteModel()

    model.TEAMS = pyo.RangeSet(1, n_teams)
    model.REQS = pyo.RangeSet(1, n_req)

    model.x = pyo.Var(model.TEAMS, within=pyo.Binary)

    def cost_rule(m):
        return sum(team_costs[t - 1] * m.x[t] for t in m.TEAMS)

    def req_rule(m, r):
        members = coverage_sets[r - 1]
        return sum(m.x[t] for t in members) >= thresholds[r - 1]

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)
    model.coverage = pyo.Constraint(model.REQS, rule=req_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}