# IR: {"sets":{"Z":"1..21","S":"1..15","C[z]":"{s in S: distance_matrix[z,s] <= coverage_radius}"},"params":{"opening_cost":"cost indexed by S, read from params","coverage_radius":"coverage threshold, read from params","distance_matrix":"distances indexed by Z x S, read from params"},"variables":{"open_station[s]":"binary for s in S"},"constraints":["coverage[z]: sum(open_station[s] for s in C[z]) >= 1 for each z in Z; infeasible if C[z] is empty"],"objective":"minimize sum(opening_cost[s] * open_station[s] for s in S)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed(data, position):
    """Accept zero-based sequences or mappings with one-based integer/string keys."""
    if isinstance(data, Mapping):
        if position in data:
            return data[position]
        return data[str(position)]
    return data[position - 1]


def solve(params):
    opening_cost = params["opening_cost"]
    coverage_radius = params["coverage_radius"]
    distance_matrix = params["distance_matrix"]

    model = pyo.ConcreteModel()
    model.zones = pyo.RangeSet(1, 21)
    model.sites = pyo.RangeSet(1, 15)

    model.opening_cost = pyo.Param(
        model.sites,
        initialize={
            site: _indexed(opening_cost, site)
            for site in model.sites
        },
    )
    model.coverage_radius = pyo.Param(initialize=coverage_radius)
    model.distance_matrix = pyo.Param(
        model.zones,
        model.sites,
        initialize={
            (zone, site): _indexed(_indexed(distance_matrix, zone), site)
            for zone in model.zones
            for site in model.sites
        },
    )

    def covering_sites_rule(instance, zone):
        return [
            site
            for site in instance.sites
            if pyo.value(instance.distance_matrix[zone, site])
            <= pyo.value(instance.coverage_radius)
        ]

    model.covering_sites = pyo.Set(
        model.zones,
        within=model.sites,
        initialize=covering_sites_rule,
    )

    model.open_station = pyo.Var(model.sites, domain=pyo.Binary)

    def coverage_rule(instance, zone):
        if len(instance.covering_sites[zone]) == 0:
            return pyo.Constraint.Infeasible
        return (
            pyo.quicksum(
                instance.open_station[site]
                for site in instance.covering_sites[zone]
            )
            >= 1
        )

    model.coverage = pyo.Constraint(model.zones, rule=coverage_rule)
    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.opening_cost[site] * model.open_station[site]
            for site in model.sites
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no solution can be loaded. Objective
        # retrieval below remains the sole test for success.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}