# IR: {"sets":{"F":"0..9","P":"0..8"},"params":{"a":"earliest landing times, indexed by F","b":"latest landing times, indexed by F"},"variables":{"t[F]":"real","d":"nonnegative real"},"constraints":["t[j] >= a[j] for j in F","t[j] <= b[j] for j in F","t[j+1] - t[j] >= d for j in P"],"objective":"maximize d"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    earliest = params["a"]
    latest = params["b"]

    if len(earliest) != 10 or len(latest) != 10:
        return {"objective": None, "status": "invalid_input_length"}

    model = pyo.ConcreteModel()

    model.flights = pyo.RangeSet(0, 9)
    model.adjacent_pairs = pyo.RangeSet(0, 8)

    model.earliest = pyo.Param(
        model.flights,
        initialize={flight: earliest[flight] for flight in range(10)},
        within=pyo.Reals,
    )
    model.latest = pyo.Param(
        model.flights,
        initialize={flight: latest[flight] for flight in range(10)},
        within=pyo.Reals,
    )

    model.landing_time = pyo.Var(model.flights, domain=pyo.Reals)
    model.minimum_separation = pyo.Var(domain=pyo.NonNegativeReals)

    def earliest_rule(instance, flight):
        return instance.landing_time[flight] >= instance.earliest[flight]

    def latest_rule(instance, flight):
        return instance.landing_time[flight] <= instance.latest[flight]

    def separation_rule(instance, flight):
        return (
            instance.landing_time[flight + 1] - instance.landing_time[flight]
            >= instance.minimum_separation
        )

    model.earliest_constraints = pyo.Constraint(
        model.flights, rule=earliest_rule
    )
    model.latest_constraints = pyo.Constraint(
        model.flights, rule=latest_rule
    )
    model.separation_constraints = pyo.Constraint(
        model.adjacent_pairs, rule=separation_rule
    )

    model.objective = pyo.Objective(
        expr=model.minimum_separation,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}