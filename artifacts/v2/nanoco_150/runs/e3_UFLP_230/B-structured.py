# IR: {"sets":{"stops":"0..17","sites":"0..4"},"params":{"installation_costs":"cost[site]","walking_distances":"distance[stop,site]","num_stops":"must equal 18","num_sites":"must equal 5"},"variables":{"opened[site]":"binary","assigned[stop,site]":"binary"},"constraints":["For each stop: sum_site assigned[stop,site] = 1.","For each stop and site: assigned[stop,site] <= opened[site]."],"objective":"minimize sum_site cost[site]*opened[site] + sum_stop,site distance[stop,site]*assigned[stop,site]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_stops = params["num_stops"]
    num_sites = params["num_sites"]
    installation_costs = params["installation_costs"]
    walking_distances = params["walking_distances"]

    if num_stops != 18 or num_sites != 5:
        return {"objective": None, "status": "invalid_dimensions"}

    model = pyo.ConcreteModel()
    model.stops = pyo.RangeSet(0, 17)
    model.sites = pyo.RangeSet(0, 4)

    model.installation_cost = pyo.Param(
        model.sites,
        initialize={
            site: installation_costs[site]
            for site in model.sites
        },
        within=pyo.Reals,
    )
    model.walking_distance = pyo.Param(
        model.stops,
        model.sites,
        initialize={
            (stop, site): walking_distances[stop][site]
            for stop in model.stops
            for site in model.sites
        },
        within=pyo.Reals,
    )

    model.opened = pyo.Var(model.sites, domain=pyo.Binary)
    model.assigned = pyo.Var(
        model.stops, model.sites, domain=pyo.Binary
    )

    def assignment_rule(instance, stop):
        return sum(
            instance.assigned[stop, site]
            for site in instance.sites
        ) == 1

    model.exactly_one_assignment = pyo.Constraint(
        model.stops, rule=assignment_rule
    )

    def installation_link_rule(instance, stop, site):
        return (
            instance.assigned[stop, site]
            <= instance.opened[site]
        )

    model.assignment_requires_installation = pyo.Constraint(
        model.stops, model.sites, rule=installation_link_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.installation_cost[site] * model.opened[site]
            for site in model.sites
        )
        + sum(
            model.walking_distance[stop, site]
            * model.assigned[stop, site]
            for stop in model.stops
            for site in model.sites
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}