# IR: {"sets":{"I":"0..19","J":"0..13","K":"{0,1}","E":"{(i,j): distances[i,j] <= coverage_radius}"},"params":{"demands":"params['demands'][i], nonnegative","zone_coords":"params['zone_coords'][i][k], real; geographic metadata","site_coords":"params['site_coords'][j][k], real; geographic metadata","distances":"params['distances'][i][j], nonnegative","coverage_radius":"params['coverage_radius'], nonnegative","num_stations":"params['num_stations'], nonnegative integer"},"variables":{"installed[j]":"binary","covered[i]":"binary"},"constraints":["sum(j in J, installed[j]) = num_stations","covered[i] <= sum(j: (i,j) in E, installed[j]) for i in I","covered[i] >= installed[j] for (i,j) in E"],"objective":"maximize sum(i in I, demands[i] * covered[i])"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
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
    model.coordinate_axes = pyo.RangeSet(0, 1)

    model.demands = pyo.Param(
        model.zones,
        initialize={i: demands[i] for i in model.zones},
        within=pyo.NonNegativeReals,
    )
    model.zone_coords = pyo.Param(
        model.zones,
        model.coordinate_axes,
        initialize={
            (i, k): zone_coords[i][k]
            for i in model.zones
            for k in model.coordinate_axes
        },
        within=pyo.Reals,
    )
    model.site_coords = pyo.Param(
        model.sites,
        model.coordinate_axes,
        initialize={
            (j, k): site_coords[j][k]
            for j in model.sites
            for k in model.coordinate_axes
        },
        within=pyo.Reals,
    )
    model.distances = pyo.Param(
        model.zones,
        model.sites,
        initialize={
            (i, j): distances[i][j]
            for i in model.zones
            for j in model.sites
        },
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

    coverage_pairs = [
        (i, j)
        for i in model.zones
        for j in model.sites
        if pyo.value(model.distances[i, j])
        <= pyo.value(model.coverage_radius)
    ]
    neighbors = {
        i: [j for zone, j in coverage_pairs if zone == i]
        for i in model.zones
    }

    model.coverage_pairs = pyo.Set(
        dimen=2,
        within=model.zones * model.sites,
        initialize=coverage_pairs,
    )

    model.installed = pyo.Var(model.sites, domain=pyo.Binary)
    model.covered = pyo.Var(model.zones, domain=pyo.Binary)

    model.station_cardinality = pyo.Constraint(
        expr=sum(model.installed[j] for j in model.sites)
        == model.num_stations
    )

    def coverage_upper_rule(model, i):
        return model.covered[i] <= sum(
            model.installed[j] for j in neighbors[i]
        )

    model.coverage_upper = pyo.Constraint(
        model.zones,
        rule=coverage_upper_rule,
    )

    def coverage_lower_rule(model, i, j):
        return model.covered[i] >= model.installed[j]

    model.coverage_lower = pyo.Constraint(
        model.coverage_pairs,
        rule=coverage_lower_rule,
    )

    model.total_covered_demand = pyo.Objective(
        expr=sum(
            model.demands[i] * model.covered[i]
            for i in model.zones
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_covered_demand))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}