import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    coverage_radius = params["coverage_radius"]
    distance_matrix = params["distance_matrix"]

    zones = list(range(1, 22))
    sites = list(range(1, 16))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(sites, domain=pyo.Binary)

    def obj_rule(model):
        return sum(opening_cost[s - 1] * model.x[s] for s in sites)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def coverage_rule(model, i):
        return sum(
            model.x[j] for j in sites
            if distance_matrix[i - 1][j - 1] <= coverage_radius
        ) >= 1

    model.coverage = pyo.Constraint(zones, rule=coverage_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}