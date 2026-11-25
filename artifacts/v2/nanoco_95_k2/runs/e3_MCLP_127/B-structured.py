# IR: {"sets":{"zones":"0..19","sites":"0..13","axes":"0..1","eligible_pairs":"{(i,j): distances[i,j] <= coverage_radius}"},"params":{"demands":"params['demands'][i], nonnegative","zone_coords":"params['zone_coords'][i][a], real, descriptive only","site_coords":"params['site_coords'][j][a], real, descriptive only","distances":"params['distances'][i][j], nonnegative, authoritative travel distances","coverage_radius":"params['coverage_radius'], nonnegative","num_stations":"params['num_stations'], nonnegative integer"},"variables":{"station_open[j]":"binary","zone_covered[i]":"binary"},"constraints":["sum_j station_open[j] = num_stations","zone_covered[i] <= sum_{j:(i,j) in eligible_pairs} station_open[j] for each zone i","zone_covered[i] >= station_open[j] for each eligible pair (i,j)"],"objective":"maximize sum_i demands[i] * zone_covered[i]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demands = params["demands"]
    zone_coords = params["zone_coords"]
    site_coords = params["site_coords"]
    distances = params["distances"]
    coverage_radius = params["coverage_radius"]
    num_stations = params["num_stations"]

    model = pyo.ConcreteModel()

    model.zones = pyo.RangeSet(0, 19)
    model.sites = pyo.RangeSet(0, 13)
    model.axes = pyo.RangeSet(0, 1)

    model.demands = pyo.Param(
        model.zones,
        initialize=lambda mdl, zone: demands[zone],
        within=pyo.NonNegativeReals,
    )
    model.zone_coords = pyo.Param(
        model.zones,
        model.axes,
        initialize=lambda mdl, zone, axis: zone_coords[zone][axis],
        within=pyo.Reals,
    )
    model.site_coords = pyo.Param(
        model.sites,
        model.axes,
        initialize=lambda mdl, site, axis: site_coords[site][axis],
        within=pyo.Reals,
    )
    model.distances = pyo.Param(
        model.zones,
        model.sites,
        initialize=lambda mdl, zone, site: distances[zone][site],
        within=pyo.NonNegativeReals,
    )
    model.coverage_radius = pyo.Param(
        initialize=coverage_radius,
        within=pyo.NonNegativeReals,
    )
    model.num_stations = pyo.Param(
        initialize=num_stations,
        within=pyo.NonNegativeIntegers,
    )

    model.eligible_pairs = pyo.Set(
        dimen=2,
        within=model.zones * model.sites,
        initialize=[
            (zone, site)
            for zone in model.zones
            for site in model.sites
            if pyo.value(model.distances[zone, site])
            <= pyo.value(model.coverage_radius)
        ],
    )

    covering_sites = {
        zone: [
            site
            for site in model.sites
            if (zone, site) in model.eligible_pairs
        ]
        for zone in model.zones
    }

    model.station_open = pyo.Var(model.sites, domain=pyo.Binary)
    model.zone_covered = pyo.Var(model.zones, domain=pyo.Binary)

    model.station_cardinality = pyo.Constraint(
        expr=sum(model.station_open[site] for site in model.sites)
        == model.num_stations
    )

    def coverage_upper_rule(mdl, zone):
        return mdl.zone_covered[zone] <= sum(
            mdl.station_open[site] for site in covering_sites[zone]
        )

    model.coverage_upper = pyo.Constraint(
        model.zones,
        rule=coverage_upper_rule,
    )

    def coverage_lower_rule(mdl, zone, site):
        return mdl.zone_covered[zone] >= mdl.station_open[site]

    model.coverage_lower = pyo.Constraint(
        model.eligible_pairs,
        rule=coverage_lower_rule,
    )

    model.total_covered_demand = pyo.Objective(
        expr=sum(
            model.demands[zone] * model.zone_covered[zone]
            for zone in model.zones
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_covered_demand))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}