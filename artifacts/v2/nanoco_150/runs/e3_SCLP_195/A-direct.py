import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    site_costs = params["site_costs"]
    coverage_radius = params["coverage_radius"]
    zone_site_distances = params["zone_site_distances"]
    num_zones = params["num_zones"]
    num_sites = params["num_sites"]

    zones = range(num_zones)
    sites = range(num_sites)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(sites, within=pyo.Binary)

    def obj_rule(mdl):
        return sum(site_costs[s] * mdl.x[s] for s in sites)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def cover_rule(mdl, z):
        return sum(
            mdl.x[s] for s in sites if zone_site_distances[z][s] <= coverage_radius
        ) >= 1

    model.coverage = pyo.Constraint(zones, rule=cover_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}