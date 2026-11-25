# IR: {"sets":{"S":"1..num_stations","V":"1..num_vehicles"},"params":{"num_stations":"params[num_stations]","num_vehicles":"params[num_vehicles]","station_x[S]":"station x-coordinates","station_y[S]":"station y-coordinates","vehicle_x[V]":"vehicle x-coordinates","vehicle_y[V]":"vehicle y-coordinates","installation_cost[S]":"fixed installation costs","station_capacity[S]":"maximum throughput","vehicle_demand[V]":"energy demands","access_cost[V,S]":"total access cost per vehicle-station assignment; not multiplied by demand"},"variables":{"build[S]":"binary","assign[V,S]":"binary"},"constraints":["single_source[v]: sum(assign[v,s] for s in S) == 1","capacity[s]: sum(vehicle_demand[v]*assign[v,s] for v in V) <= station_capacity[s]*build[s]","open_link[v,s]: assign[v,s] <= build[s]"],"objective":"minimize sum(installation_cost[s]*build[s] for s in S) + sum(access_cost[v,s]*assign[v,s] for v in V for s in S)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-based input sequences and a vehicle-by-station matrix."""
    num_stations = int(params["num_stations"])
    num_vehicles = int(params["num_vehicles"])

    station_x = params["station_x"]
    station_y = params["station_y"]
    vehicle_x = params["vehicle_x"]
    vehicle_y = params["vehicle_y"]
    installation_cost = params["installation_cost"]
    station_capacity = params["station_capacity"]
    vehicle_demand = params["vehicle_demand"]
    access_cost = params["access_cost"]

    model = pyo.ConcreteModel()
    model.S = pyo.RangeSet(1, num_stations)
    model.V = pyo.RangeSet(1, num_vehicles)

    # Coordinates are retained as input data. The supplied access-cost matrix
    # already determines assignment costs, so distances are not recomputed.
    model.station_x = pyo.Param(
        model.S,
        initialize={s: station_x[s - 1] for s in model.S},
        within=pyo.Reals,
    )
    model.station_y = pyo.Param(
        model.S,
        initialize={s: station_y[s - 1] for s in model.S},
        within=pyo.Reals,
    )
    model.vehicle_x = pyo.Param(
        model.V,
        initialize={v: vehicle_x[v - 1] for v in model.V},
        within=pyo.Reals,
    )
    model.vehicle_y = pyo.Param(
        model.V,
        initialize={v: vehicle_y[v - 1] for v in model.V},
        within=pyo.Reals,
    )
    model.installation_cost = pyo.Param(
        model.S,
        initialize={s: installation_cost[s - 1] for s in model.S},
        within=pyo.Reals,
    )
    model.station_capacity = pyo.Param(
        model.S,
        initialize={s: station_capacity[s - 1] for s in model.S},
        within=pyo.NonNegativeReals,
    )
    model.vehicle_demand = pyo.Param(
        model.V,
        initialize={v: vehicle_demand[v - 1] for v in model.V},
        within=pyo.NonNegativeReals,
    )
    model.access_cost = pyo.Param(
        model.V,
        model.S,
        initialize={
            (v, s): access_cost[v - 1][s - 1]
            for v in model.V
            for s in model.S
        },
        within=pyo.Reals,
    )

    model.build = pyo.Var(model.S, domain=pyo.Binary)
    model.assign = pyo.Var(model.V, model.S, domain=pyo.Binary)

    def single_source_rule(problem, v):
        return sum(problem.assign[v, s] for s in problem.S) == 1

    model.single_source = pyo.Constraint(model.V, rule=single_source_rule)

    def capacity_rule(problem, s):
        return (
            sum(
                problem.vehicle_demand[v] * problem.assign[v, s]
                for v in problem.V
            )
            <= problem.station_capacity[s] * problem.build[s]
        )

    model.capacity = pyo.Constraint(model.S, rule=capacity_rule)

    def open_link_rule(problem, v, s):
        return problem.assign[v, s] <= problem.build[s]

    model.open_link = pyo.Constraint(model.V, model.S, rule=open_link_rule)

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.installation_cost[s] * model.build[s]
                for s in model.S
            )
            + sum(
                model.access_cost[v, s] * model.assign[v, s]
                for v in model.V
                for s in model.S
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}