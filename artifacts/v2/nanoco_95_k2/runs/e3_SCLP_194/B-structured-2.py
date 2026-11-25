# IR: {"sets":{"communities":"1..28","sites":"1..10"},"params":{"establishment_cost":"site-indexed costs from params['establishment_cost']","coverage_radius":"scalar from params['coverage_radius']","distance_matrix":"community-by-site distances from params['distance_matrix']","covered":"1 if distance_matrix[i,j] <= coverage_radius else 0"},"variables":{"open_depot[j]":"Binary"},"constraints":["For each community i: sum(covered[i,j] * open_depot[j] for j in sites) >= 1"],"objective":"Minimize sum(establishment_cost[j] * open_depot[j] for j in sites)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the minimum-cost depot coverage problem using ordered input arrays."""
    establishment_cost = params["establishment_cost"]
    coverage_radius = params["coverage_radius"]
    distance_matrix = params["distance_matrix"]

    model = pyo.ConcreteModel()

    model.communities = pyo.RangeSet(1, 28)
    model.sites = pyo.RangeSet(1, 10)

    model.establishment_cost = pyo.Param(
        model.sites,
        initialize={
            site: float(establishment_cost[site - 1])
            for site in model.sites
        },
        within=pyo.Reals,
    )
    model.coverage_radius = pyo.Param(
        initialize=float(coverage_radius),
        within=pyo.NonNegativeReals,
    )
    model.distance_matrix = pyo.Param(
        model.communities,
        model.sites,
        initialize={
            (community, site): float(
                distance_matrix[community - 1][site - 1]
            )
            for community in model.communities
            for site in model.sites
        },
        within=pyo.NonNegativeReals,
    )

    def covered_initializer(instance, community, site):
        return int(
            pyo.value(instance.distance_matrix[community, site])
            <= pyo.value(instance.coverage_radius)
        )

    model.covered = pyo.Param(
        model.communities,
        model.sites,
        initialize=covered_initializer,
        within=pyo.Binary,
    )

    model.open_depot = pyo.Var(model.sites, domain=pyo.Binary)

    def universal_coverage_rule(instance, community):
        return pyo.quicksum(
            instance.covered[community, site] * instance.open_depot[site]
            for site in instance.sites
        ) >= 1

    model.universal_coverage = pyo.Constraint(
        model.communities,
        rule=universal_coverage_rule,
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.establishment_cost[site] * model.open_depot[site]
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