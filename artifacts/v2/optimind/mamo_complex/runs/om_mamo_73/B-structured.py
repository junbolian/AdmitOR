# IR: {"sets":{"N":"0..8","A":"(i,j) with i != j and capacity[i,j] > 0","T":"1..7"},"params":{"capacity":"finite nonnegative directed capacities read from params['capacity']; omitted links are zero; absent parameter returns missing_capacity"},"variables":{"flow[i,j]":"nonnegative real for (i,j) in A","throughput":"nonnegative real"},"constraints":["flow[i,j] <= capacity[i,j] for each arc","outflow(0) - inflow(0) = throughput","inflow(8) - outflow(8) = throughput","outflow(i) = inflow(i) for each i in T"],"objective":"maximize throughput"}
from collections.abc import Mapping
import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Compute the maximum flow from station 0 to station 8.

    Accepted params["capacity"] formats:
      - A 9-by-9 sequence.
      - A mapping {(i, j): capacity}.
      - A nested mapping {i: {j: capacity}}, using integer or string indices.
      - A mapping {"i,j": capacity}.

    Missing mapping entries represent zero-capacity links.
    The capacity parameter itself must be supplied; its values are never
    inferred or hardcoded.
    """
    if "capacity" not in params:
        return {"objective": None, "status": "missing_capacity"}

    raw_capacity = params["capacity"]
    if raw_capacity is None:
        return {"objective": None, "status": "missing_capacity"}

    nodes = tuple(range(9))

    def capacity_at(origin, destination):
        if isinstance(raw_capacity, Mapping):
            pair = (origin, destination)
            if pair in raw_capacity:
                return raw_capacity[pair]

            text_pair = f"{origin},{destination}"
            if text_pair in raw_capacity:
                return raw_capacity[text_pair]

            row = raw_capacity.get(origin, raw_capacity.get(str(origin), {}))
            if isinstance(row, Mapping):
                return row.get(destination, row.get(str(destination), 0))
            return row[destination]

        return raw_capacity[origin][destination]

    capacities = {}
    for origin in nodes:
        for destination in nodes:
            if origin == destination:
                continue
            value = float(capacity_at(origin, destination))
            if not math.isfinite(value) or value < 0:
                return {"objective": None, "status": "invalid_capacity"}
            if value > 0:
                capacities[origin, destination] = value

    outgoing = {
        station: tuple(arc for arc in capacities if arc[0] == station)
        for station in nodes
    }
    incoming = {
        station: tuple(arc for arc in capacities if arc[1] == station)
        for station in nodes
    }

    model = pyo.ConcreteModel()
    model.stations = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=capacities, ordered=True)
    model.transit_stations = pyo.Set(initialize=range(1, 8), ordered=True)

    model.link_capacity = pyo.Param(
        model.arcs,
        initialize=capacities,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.link_capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    def net_outflow(network, station):
        return (
            pyo.quicksum(network.flow[arc] for arc in outgoing[station])
            - pyo.quicksum(network.flow[arc] for arc in incoming[station])
        )

    model.source_balance = pyo.Constraint(
        expr=net_outflow(model, 0) == model.throughput
    )
    model.destination_balance = pyo.Constraint(
        expr=-net_outflow(model, 8) == model.throughput
    )

    def conservation_rule(network, station):
        if not outgoing[station] and not incoming[station]:
            return pyo.Constraint.Feasible
        return net_outflow(network, station) == 0

    model.flow_conservation = pyo.Constraint(
        model.transit_stations,
        rule=conservation_rule,
    )
    model.total_flow = pyo.Objective(
        expr=model.throughput,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # Allow objective retrieval to determine success after a known
        # solution-loading failure; propagate unrelated runtime errors.
        if "a feasible solution was not found" not in str(error).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}