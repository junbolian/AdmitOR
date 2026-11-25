# IR: {"sets":{"I":"1..29","J":"1..10","C1[i]":"{j: travel_time[i,j] <= critical_response_threshold_R1}","C2[i]":"{j: travel_time[i,j] <= premium_response_threshold_R2}"},"params":{"construction_cost":"J -> real","demand_weight":"I -> real; informational, already reflected in the supplied premium benefits","premium_benefit":"I -> real","critical_response_threshold_R1":"real","premium_response_threshold_R2":"real","travel_time":"I x J -> real"},"variables":{"build[j]":"binary","premium[i]":"binary"},"constraints":["For each i: sum(build[j] for j in C1[i]) >= 1; an empty C1[i] is infeasible.","For each i: premium[i] <= sum(build[j] for j in C2[i]).","For each i and j in C2[i]: premium[i] >= build[j]."],"objective":"minimize sum(construction_cost[j]*build[j] for j in J) - sum(premium_benefit[i]*premium[i] for i in I)"}

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


def _matrix_entry(data, resident, site):
    """Also accept a matrix mapping keyed by (resident, site) tuples."""
    if isinstance(data, Mapping) and (resident, site) in data:
        return data[(resident, site)]
    return _indexed(_indexed(data, resident), site)


def solve(params):
    construction_cost = params["construction_cost"]
    demand_weight = params["demand_weight"]
    premium_benefit = params["premium_benefit"]
    critical_threshold = float(params["critical_response_threshold_R1"])
    premium_threshold = float(params["premium_response_threshold_R2"])
    travel_time = params["travel_time"]

    model = pyo.ConcreteModel()

    model.residents = pyo.RangeSet(1, 29)
    model.sites = pyo.RangeSet(1, 10)

    model.construction_cost = pyo.Param(
        model.sites,
        initialize=lambda mdl, site: float(_indexed(construction_cost, site)),
        within=pyo.Reals,
    )
    model.demand_weight = pyo.Param(
        model.residents,
        initialize=lambda mdl, resident: float(_indexed(demand_weight, resident)),
        within=pyo.Reals,
    )
    model.premium_benefit = pyo.Param(
        model.residents,
        initialize=lambda mdl, resident: float(_indexed(premium_benefit, resident)),
        within=pyo.Reals,
    )
    model.critical_threshold = pyo.Param(initialize=critical_threshold)
    model.premium_threshold = pyo.Param(initialize=premium_threshold)
    model.travel_time = pyo.Param(
        model.residents,
        model.sites,
        initialize=lambda mdl, resident, site: float(
            _matrix_entry(travel_time, resident, site)
        ),
        within=pyo.Reals,
    )

    model.critical_sites = pyo.Set(
        model.residents,
        within=model.sites,
        initialize=lambda mdl, resident: [
            site
            for site in mdl.sites
            if pyo.value(mdl.travel_time[resident, site])
            <= pyo.value(mdl.critical_threshold)
        ],
    )
    model.premium_sites = pyo.Set(
        model.residents,
        within=model.sites,
        initialize=lambda mdl, resident: [
            site
            for site in mdl.sites
            if pyo.value(mdl.travel_time[resident, site])
            <= pyo.value(mdl.premium_threshold)
        ],
    )

    model.build = pyo.Var(model.sites, domain=pyo.Binary)
    model.premium = pyo.Var(model.residents, domain=pyo.Binary)

    def critical_coverage_rule(mdl, resident):
        if len(mdl.critical_sites[resident]) == 0:
            return pyo.Constraint.Infeasible
        return (
            pyo.quicksum(
                mdl.build[site] for site in mdl.critical_sites[resident]
            )
            >= 1
        )

    model.critical_coverage = pyo.Constraint(
        model.residents, rule=critical_coverage_rule
    )

    model.premium_upper = pyo.Constraint(
        model.residents,
        rule=lambda mdl, resident: mdl.premium[resident]
        <= pyo.quicksum(
            mdl.build[site] for site in mdl.premium_sites[resident]
        ),
    )

    model.premium_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (resident, site)
            for resident in model.residents
            for site in model.premium_sites[resident]
        ],
    )
    model.premium_lower = pyo.Constraint(
        model.premium_pairs,
        rule=lambda mdl, resident, site: mdl.premium[resident]
        >= mdl.build[site],
    )

    # premium_benefit is the total bonus per resident population; multiplying
    # it by demand_weight again would double-count the demand weighting.
    model.net_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.construction_cost[site] * model.build[site]
            for site in model.sites
        )
        - pyo.quicksum(
            model.premium_benefit[resident] * model.premium[resident]
            for resident in model.residents
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when no feasible solution can be loaded.
        # Other runtime errors are unexpected and should propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.net_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}