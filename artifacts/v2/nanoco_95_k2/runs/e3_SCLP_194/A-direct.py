import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    establishment_cost = params["establishment_cost"]
    coverage_radius = params["coverage_radius"]
    distance_matrix = params["distance_matrix"]

    n_communities = len(distance_matrix)
    n_sites = len(establishment_cost)

    model = pyo.ConcreteModel()

    model.communities = pyo.RangeSet(0, n_communities - 1)
    model.sites = pyo.RangeSet(0, n_sites - 1)

    model.open_depot = pyo.Var(model.sites, domain=pyo.Binary)

    def objective_rule(m):
        return sum(establishment_cost[j] * m.open_depot[j] for j in m.sites)

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def coverage_rule(m, i):
        return sum(
            m.open_depot[j]
            for j in m.sites
            if distance_matrix[i][j] <= coverage_radius
        ) >= 1

    model.cover = pyo.Constraint(model.communities, rule=coverage_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}