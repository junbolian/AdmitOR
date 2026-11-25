import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_costs = params["opening_costs"]
    coverage_radius = params["coverage_radius"]
    distance_matrix = params["distance_matrix"]

    num_zones = len(distance_matrix)
    num_sites = len(opening_costs)

    model = pyo.ConcreteModel()

    model.ZONES = pyo.RangeSet(0, num_zones - 1)
    model.SITES = pyo.RangeSet(0, num_sites - 1)

    model.x = pyo.Var(model.SITES, domain=pyo.Binary)

    def cover_rule(mdl, i):
        return sum(
            mdl.x[j]
            for j in mdl.SITES
            if distance_matrix[i][j] <= coverage_radius
        ) >= 1

    model.cover = pyo.Constraint(model.ZONES, rule=cover_rule)

    model.cost = pyo.Objective(
        expr=sum(opening_costs[j] * model.x[j] for j in model.SITES),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}