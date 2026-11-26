# IR: {"sets":{"cities":"0..7","arcs":"all ordered pairs (i,j), i != j"},"params":{"capacity":"params['capacity']; nonnegative capacities in thousands/hour; accepts an 8x8 matrix, 64 row-major entries, 56 off-diagonal row-major entries, or 55 entries in the problem's listed order (omitted arc 0->7 has zero capacity)"},"variables":{"flow[i,j]":"nonnegative continuous on arcs","throughput":"nonnegative continuous"},"constraints":["flow[i,j] <= capacity[i,j] for every arc","outflow[i]-inflow[i] = throughput at city 0, -throughput at city 7, and 0 at every other city"],"objective":"maximize throughput"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity_data = params["capacity"]
    cities = list(range(8))
    arcs = [
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    ]

    if len(capacity_data) == 8:
        if any(len(row) != 8 for row in capacity_data):
            raise ValueError("The capacity matrix must have eight columns per row.")
        capacities = {
            (origin, destination): capacity_data[origin][destination]
            for origin, destination in arcs
        }
    elif len(capacity_data) == 64:
        capacities = {
            (origin, destination): capacity_data[8 * origin + destination]
            for origin, destination in arcs
        }
    elif len(capacity_data) == 56:
        capacities = dict(zip(arcs, capacity_data))
    elif len(capacity_data) == 55:
        listed_arcs = [
            (origin, destination)
            for origin, destination in arcs
            if (origin, destination) != (0, 7)
        ]
        capacities = dict(zip(listed_arcs, capacity_data))
        capacities[0, 7] = 0
    else:
        raise ValueError(
            "capacity must be an 8x8 matrix or a flat sequence "
            "containing 64, 56, or 55 entries."
        )

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacities,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(mdl, origin, destination):
        return mdl.flow[origin, destination] <= mdl.capacity[origin, destination]

    model.capacity_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    def conservation_rule(mdl, city):
        outgoing = sum(
            mdl.flow[city, destination]
            for destination in mdl.cities
            if destination != city
        )
        incoming = sum(
            mdl.flow[origin, city]
            for origin in mdl.cities
            if origin != city
        )
        if city == 0:
            return outgoing - incoming == mdl.throughput
        if city == 7:
            return outgoing - incoming == -mdl.throughput
        return outgoing - incoming == 0

    model.flow_balance = pyo.Constraint(model.cities, rule=conservation_rule)
    model.max_throughput = pyo.Objective(
        expr=model.throughput,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.max_throughput))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}