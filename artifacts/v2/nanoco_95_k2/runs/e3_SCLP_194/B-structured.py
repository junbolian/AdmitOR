# IR: {"sets":{"communities":"1..28","sites":"1..10"},"params":{"establishment_cost":"params['establishment_cost'][j-1]","coverage_radius":"params['coverage_radius']","distance_matrix":"params['distance_matrix'][i-1][j-1]"},"derived":{"covered[i,j]":"1 if distance_matrix[i,j] <= coverage_radius else 0"},"variables":{"open_site[j]":"Binary"},"constraints":["For each community i: sum(covered[i,j] * open_site[j] for j in sites) >= 1"],"objective":"Minimize sum(establishment_cost[j] * open_site[j] for j in sites)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    establishment_cost = params["establishment_cost"]
    coverage_radius = params["coverage_radius"]
    distance_matrix = params["distance_matrix"]

    model = pyo.ConcreteModel()

    model.communities = pyo.RangeSet(1, 28)
    model.sites = pyo.RangeSet(1, 10)

    model.establishment_cost = pyo.Param(
        model.sites,
        initialize=lambda model, site: establishment_cost[site - 1],
        within=pyo.Reals,
    )
    model.coverage_radius = pyo.Param(
        initialize=coverage_radius,
        within=pyo.NonNegativeReals,
    )
    model.distance_matrix = pyo.Param(
        model.communities,
        model.sites,
        initialize=lambda model, community, site: (
            distance_matrix[community - 1][site - 1]
        ),
        within=pyo.NonNegativeReals,
    )

    def covered_initializer(model, community, site):
        return int(
            pyo.value(model.distance_matrix[community, site])
            <= pyo.value(model.coverage_radius)
        )

    model.covered = pyo.Param(
        model.communities,
        model.sites,
        initialize=covered_initializer,
        within=pyo.Binary,
    )

    model.open_site = pyo.Var(model.sites, domain=pyo.Binary)

    def universal_coverage_rule(model, community):
        return pyo.quicksum(
            model.covered[community, site] * model.open_site[site]
            for site in model.sites
        ) >= 1

    model.universal_coverage = pyo.Constraint(
        model.communities,
        rule=universal_coverage_rule,
    )

    model.total_establishment_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.establishment_cost[site] * model.open_site[site]
            for site in model.sites
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_establishment_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}