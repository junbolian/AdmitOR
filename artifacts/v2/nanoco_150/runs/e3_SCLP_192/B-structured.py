# IR: {"sets":{"zones":"1..20","sites":"1..14","covering_sites[i]":"{j in sites: distance_matrix[i,j] <= coverage_radius}"},"params":{"opening_costs":"params['opening_costs'], length-14 sequence","coverage_radius":"params['coverage_radius'], scalar","distance_matrix":"params['distance_matrix'], 20x14 sequence"},"variables":{"deploy[j]":"binary for j in sites"},"constraints":["coverage[i]: sum(deploy[j] for j in covering_sites[i]) >= 1 for every zone i"],"objective":"minimize sum(opening_costs[j] * deploy[j] for j in sites)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the tower set-covering problem using zero-based input sequences."""
    opening_costs = params["opening_costs"]
    coverage_radius = params["coverage_radius"]
    distance_matrix = params["distance_matrix"]

    model = pyo.ConcreteModel()

    model.zones = pyo.RangeSet(1, 20)
    model.sites = pyo.RangeSet(1, 14)

    model.opening_costs = pyo.Param(
        model.sites,
        initialize=lambda mdl, site: opening_costs[site - 1],
        within=pyo.Reals,
    )
    model.coverage_radius = pyo.Param(
        initialize=coverage_radius,
        within=pyo.NonNegativeReals,
    )
    model.distance_matrix = pyo.Param(
        model.zones,
        model.sites,
        initialize=lambda mdl, zone, site: distance_matrix[zone - 1][site - 1],
        within=pyo.NonNegativeReals,
    )

    def covering_sites_rule(mdl, zone):
        return [
            site
            for site in mdl.sites
            if pyo.value(mdl.distance_matrix[zone, site])
            <= pyo.value(mdl.coverage_radius)
        ]

    model.covering_sites = pyo.Set(
        model.zones,
        within=model.sites,
        initialize=covering_sites_rule,
    )

    model.deploy = pyo.Var(model.sites, domain=pyo.Binary)

    def coverage_rule(mdl, zone):
        # Tuple form also represents an infeasible constraint when no site covers
        # a zone, without evaluating a constant comparison to a Python boolean.
        return (
            1,
            pyo.quicksum(mdl.deploy[site] for site in mdl.covering_sites[zone]),
            None,
        )

    model.coverage = pyo.Constraint(model.zones, rule=coverage_rule)

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.opening_costs[site] * model.deploy[site]
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