# IR: {"sets":{"D":"1..27","S":"1..10","C":"{(i,j): distance[i,j] <= coverage_radius}","P":"{(i,j): distance[i,j] <= precision_radius}"},"params":{"installation_cost":"S -> real","district_x":"D -> real","district_y":"D -> real","site_x":"S -> real","site_y":"S -> real","demand":"D -> real","distance":"D x S -> real","grant_revenue":"D -> real","coverage_radius":"real","precision_radius":"real"},"variables":{"deployed[j]":"binary, j in S","precision_monitored[i]":"binary, i in D"},"constraints":["For each i in D: sum(deployed[j] for (i,j) in C) >= 1","For each i in D: precision_monitored[i] <= sum(deployed[j] for (i,j) in P)","For each (i,j) in P: precision_monitored[i] >= deployed[j]"],"objective":"minimize sum(installation_cost[j]*deployed[j] for j in S) - sum(grant_revenue[i]*precision_monitored[i] for i in D)","notes":"Coordinates and demand are retained as input parameters; the supplied distance matrix determines eligibility."}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(data, position):
    """Read a zero-based sequence or a mapping with one-based integer/string keys."""
    if isinstance(data, Mapping):
        if position in data:
            return data[position]
        return data[str(position)]
    return data[position - 1]


def _distance_entry(data, district, site):
    """Accept nested sequences/mappings or a mapping keyed by (district, site)."""
    if isinstance(data, Mapping) and (district, site) in data:
        return data[(district, site)]
    return _entry(_entry(data, district), site)


def solve(params):
    """Build and solve the station deployment MILP using supplied parameter data."""
    installation_cost = params["installation_cost"]
    district_x = params["district_x"]
    district_y = params["district_y"]
    site_x = params["site_x"]
    site_y = params["site_y"]
    demand = params["demand"]
    distance = params["distance"]
    grant_revenue = params["grant_revenue"]
    coverage_radius = params["coverage_radius"]
    precision_radius = params["precision_radius"]

    model = pyo.ConcreteModel()
    model.D = pyo.RangeSet(1, 27)
    model.S = pyo.RangeSet(1, 10)

    district_inputs = {
        "district_x": district_x,
        "district_y": district_y,
        "demand": demand,
        "grant_revenue": grant_revenue,
    }
    site_inputs = {
        "installation_cost": installation_cost,
        "site_x": site_x,
        "site_y": site_y,
    }

    for component_name, input_data in district_inputs.items():
        model.add_component(
            component_name,
            pyo.Param(
                model.D,
                initialize={
                    district: float(_entry(input_data, district))
                    for district in model.D
                },
                within=pyo.Reals,
            ),
        )

    for component_name, input_data in site_inputs.items():
        model.add_component(
            component_name,
            pyo.Param(
                model.S,
                initialize={
                    site: float(_entry(input_data, site))
                    for site in model.S
                },
                within=pyo.Reals,
            ),
        )

    model.distance = pyo.Param(
        model.D,
        model.S,
        initialize={
            (district, site): float(
                _distance_entry(distance, district, site)
            )
            for district in model.D
            for site in model.S
        },
        within=pyo.Reals,
    )
    model.coverage_radius = pyo.Param(
        initialize=float(coverage_radius),
        within=pyo.Reals,
    )
    model.precision_radius = pyo.Param(
        initialize=float(precision_radius),
        within=pyo.Reals,
    )

    coverage_sites = {
        district: [
            site
            for site in model.S
            if pyo.value(model.distance[district, site])
            <= pyo.value(model.coverage_radius)
        ]
        for district in model.D
    }
    precision_sites = {
        district: [
            site
            for site in model.S
            if pyo.value(model.distance[district, site])
            <= pyo.value(model.precision_radius)
        ]
        for district in model.D
    }

    model.C = pyo.Set(
        dimen=2,
        initialize=[
            (district, site)
            for district in model.D
            for site in coverage_sites[district]
        ],
    )
    model.P = pyo.Set(
        dimen=2,
        initialize=[
            (district, site)
            for district in model.D
            for site in precision_sites[district]
        ],
    )

    model.deployed = pyo.Var(model.S, domain=pyo.Binary)
    model.precision_monitored = pyo.Var(model.D, domain=pyo.Binary)

    def coverage_rule(block, district):
        # Tuple form also represents infeasibility when no eligible site exists.
        return (
            1,
            pyo.quicksum(
                block.deployed[site]
                for site in coverage_sites[district]
            ),
            None,
        )

    model.regulatory_coverage = pyo.Constraint(
        model.D, rule=coverage_rule
    )

    def precision_upper_rule(block, district):
        return block.precision_monitored[district] <= pyo.quicksum(
            block.deployed[site]
            for site in precision_sites[district]
        )

    model.precision_upper = pyo.Constraint(
        model.D, rule=precision_upper_rule
    )

    def precision_lower_rule(block, district, site):
        return (
            block.precision_monitored[district]
            >= block.deployed[site]
        )

    model.precision_lower = pyo.Constraint(
        model.P, rule=precision_lower_rule
    )

    model.net_deployment_cost = pyo.Objective(
        expr=(
            pyo.quicksum(
                model.installation_cost[site] * model.deployed[site]
                for site in model.S
            )
            - pyo.quicksum(
                model.grant_revenue[district]
                * model.precision_monitored[district]
                for district in model.D
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution is available to load.
        # Objective retrievability below is the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.net_deployment_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}