import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    establishment_cost = params["establishment_cost"]
    coverage_radius = params["coverage_radius"]
    distance_matrix = params["distance_matrix"]

    num_communities = 28
    num_sites = 10

    model = pyo.ConcreteModel()

    model.communities = pyo.RangeSet(1, num_communities)
    model.sites = pyo.RangeSet(1, num_sites)

    model.open_site = pyo.Var(model.sites, domain=pyo.Binary)

    def objective_rule(m):
        return sum(establishment_cost[j - 1] * m.open_site[j] for j in m.sites)

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def coverage_rule(m, i):
        return sum(
            m.open_site[j]
            for j in m.sites
            if distance_matrix[i - 1][j - 1] <= coverage_radius
        ) >= 1

    model.coverage = pyo.Constraint(model.communities, rule=coverage_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}