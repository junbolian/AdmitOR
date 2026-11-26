# IR: {"sets":{"J":"1..n","K":"1..n-1"},"params":{"n":"params['n']","a[j]":"params['a'], indexed in flight order","b[j]":"params['b'], indexed in flight order"},"variables":{"landing[j]":"continuous real","separation":"continuous nonnegative"},"constraints":["landing[j] >= a[j] for j in J","landing[j] <= b[j] for j in J","landing[j+1] - landing[j] >= separation for j in K"],"objective":"maximize separation"}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = int(params["n"])
    a_data = params["a"]
    b_data = params["b"]

    def flight_value(data, flight):
        """Accept sequences or mappings keyed by 1-based flight numbers."""
        if isinstance(data, Mapping):
            key = flight if flight in data else str(flight)
            return float(data[key])
        return float(data[flight - 1])

    model = pyo.ConcreteModel()
    model.flights = pyo.RangeSet(1, n)
    model.adjacent_flights = pyo.RangeSet(1, n - 1)

    model.earliest = pyo.Param(
        model.flights,
        initialize={
            flight: flight_value(a_data, flight)
            for flight in model.flights
        },
        within=pyo.Reals,
    )
    model.latest = pyo.Param(
        model.flights,
        initialize={
            flight: flight_value(b_data, flight)
            for flight in model.flights
        },
        within=pyo.Reals,
    )

    model.landing = pyo.Var(model.flights, domain=pyo.Reals)
    model.separation = pyo.Var(domain=pyo.NonNegativeReals)

    def earliest_rule(instance, flight):
        return instance.landing[flight] >= instance.earliest[flight]

    def latest_rule(instance, flight):
        return instance.landing[flight] <= instance.latest[flight]

    def separation_rule(instance, flight):
        return (
            instance.landing[flight + 1] - instance.landing[flight]
            >= instance.separation
        )

    model.earliest_limits = pyo.Constraint(
        model.flights, rule=earliest_rule
    )
    model.latest_limits = pyo.Constraint(
        model.flights, rule=latest_rule
    )
    model.separation_limits = pyo.Constraint(
        model.adjacent_flights, rule=separation_rule
    )
    model.objective = pyo.Objective(
        expr=model.separation, sense=pyo.maximize
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    # Preserve the exact optimized objective in the required return value.
    # Its nearest-time-unit presentation is round(obj_val).
    return {"objective": obj_val, "status": "optimal"}