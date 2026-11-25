import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    establishment_costs = params["establishment_costs"]
    coverage_radius = params["coverage_radius"]
    distance_matrix = params["distance_matrix"]

    num_zones = len(distance_matrix)
    num_candidates = len(establishment_costs)

    model = pyo.ConcreteModel()

    model.candidates = pyo.Set(initialize=range(num_candidates))
    model.zones = pyo.Set(initialize=range(num_zones))

    model.open_station = pyo.Var(model.candidates, domain=pyo.Binary)

    def coverage_rule(mdl, z):
        return sum(
            mdl.open_station[c]
            for c in mdl.candidates
            if distance_matrix[z][c] <= coverage_radius
        ) >= 1
    model.coverage = pyo.Constraint(model.zones, rule=coverage_rule)

    def cost_rule(mdl):
        return sum(
            establishment_costs[c] * mdl.open_station[c]
            for c in mdl.candidates
        )
    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}