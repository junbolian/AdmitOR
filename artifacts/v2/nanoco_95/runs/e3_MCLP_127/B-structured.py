# IR: {"sets":{"zones":"0..19","sites":"0..13","coverage_links":"{(i,j): distance_matrix[i][j] <= coverage_radius}"},"params":{"demands":"nonnegative demand indexed by zones","coverage_radius":"nonnegative maximum covered distance","distance_matrix":"nonnegative distance indexed by zones and sites","num_stations_to_install":"nonnegative integer exact station count"},"variables":{"installed[j]":"binary","covered[i]":"binary"},"constraints":["sum_j installed[j] == num_stations_to_install","covered[i] <= sum_{j:(i,j) in coverage_links} installed[j] for each zone i","covered[i] >= installed[j] for each (i,j) in coverage_links"],"objective":"maximize sum_i demands[i] * covered[i]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demands = params["demands"]
    coverage_radius = params["coverage_radius"]
    distance_matrix = params["distance_matrix"]
    num_stations_to_install = params["num_stations_to_install"]

    model = pyo.ConcreteModel()

    model.zones = pyo.RangeSet(0, 19)
    model.sites = pyo.RangeSet(0, 13)

    model.demand = pyo.Param(
        model.zones,
        initialize=lambda mdl, i: demands[i],
        within=pyo.NonNegativeReals,
    )
    model.radius = pyo.Param(
        initialize=coverage_radius,
        within=pyo.NonNegativeReals,
    )
    model.travel_distance = pyo.Param(
        model.zones,
        model.sites,
        initialize=lambda mdl, i, j: distance_matrix[i][j],
        within=pyo.NonNegativeReals,
    )
    model.station_count = pyo.Param(
        initialize=num_stations_to_install,
        within=pyo.NonNegativeIntegers,
    )

    model.coverage_links = pyo.Set(
        dimen=2,
        within=model.zones * model.sites,
        initialize=[
            (i, j)
            for i in model.zones
            for j in model.sites
            if pyo.value(model.travel_distance[i, j])
            <= pyo.value(model.radius)
        ],
    )

    covering_sites = {
        i: [j for j in model.sites if (i, j) in model.coverage_links]
        for i in model.zones
    }

    model.installed = pyo.Var(model.sites, domain=pyo.Binary)
    model.covered = pyo.Var(model.zones, domain=pyo.Binary)

    model.exact_station_count = pyo.Constraint(
        expr=sum(model.installed[j] for j in model.sites)
        == model.station_count
    )

    model.coverage_upper_bound = pyo.Constraint(
        model.zones,
        rule=lambda mdl, i: mdl.covered[i]
        <= sum(mdl.installed[j] for j in covering_sites[i]),
    )

    model.coverage_lower_bound = pyo.Constraint(
        model.coverage_links,
        rule=lambda mdl, i, j: mdl.covered[i] >= mdl.installed[j],
    )

    model.total_covered_demand = pyo.Objective(
        expr=sum(
            model.demand[i] * model.covered[i]
            for i in model.zones
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_covered_demand))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}