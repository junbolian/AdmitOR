import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    establishment_costs = params["establishment_costs"]
    coverage_radius = params["coverage_radius"]
    distance_matrix = params["distance_matrix"]

    num_zones = len(distance_matrix)
    num_candidates = len(establishment_costs)

    zones = list(range(num_zones))
    candidates = list(range(num_candidates))

    model = pyo.ConcreteModel()

    model.zones = pyo.Set(initialize=zones)
    model.candidates = pyo.Set(initialize=candidates)

    model.x = pyo.Var(model.candidates, domain=pyo.Binary)

    def coverage_rule(m, z):
        return sum(m.x[c] for c in m.candidates if distance_matrix[z][c] <= coverage_radius) >= 1

    model.coverage = pyo.Constraint(model.zones, rule=coverage_rule)

    def obj_rule(m):
        return sum(establishment_costs[c] * m.x[c] for c in m.candidates)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}