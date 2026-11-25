# IR: {"sets":{"drivers":"0..18","sites":"0..4"},"params":{"location_investment_cost":"nonnegative[sites], from params","distance_matrix":"nonnegative[drivers,sites], from params"},"variables":{"station_open":"binary[sites]","assigned":"binary[drivers,sites]"},"constraints":["forall i: sum_j assigned[i,j] == 1","forall i,j: assigned[i,j] <= station_open[j]"],"objective":"minimize sum_j location_investment_cost[j]*station_open[j] + sum_i,j distance_matrix[i,j]*assigned[i,j]"}
import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.drivers = pyo.RangeSet(0, 18)
    model.sites = pyo.RangeSet(0, 4)

    model.investment_cost = pyo.Param(
        model.sites,
        initialize={
            site: params["location_investment_cost"][site]
            for site in model.sites
        },
        within=pyo.NonNegativeReals,
    )
    model.travel_distance = pyo.Param(
        model.drivers,
        model.sites,
        initialize={
            (driver, site): params["distance_matrix"][driver][site]
            for driver in model.drivers
            for site in model.sites
        },
        within=pyo.NonNegativeReals,
    )

    model.station_open = pyo.Var(model.sites, domain=pyo.Binary)
    model.assigned = pyo.Var(
        model.drivers, model.sites, domain=pyo.Binary
    )

    def assignment_rule(instance, driver):
        return sum(
            instance.assigned[driver, site] for site in instance.sites
        ) == 1

    model.exactly_one_station = pyo.Constraint(
        model.drivers, rule=assignment_rule
    )

    def operational_rule(instance, driver, site):
        return (
            instance.assigned[driver, site]
            <= instance.station_open[site]
        )

    model.assignment_requires_open_station = pyo.Constraint(
        model.drivers, model.sites, rule=operational_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.investment_cost[site] * model.station_open[site]
            for site in model.sites
        )
        + sum(
            model.travel_distance[driver, site]
            * model.assigned[driver, site]
            for driver in model.drivers
            for site in model.sites
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}