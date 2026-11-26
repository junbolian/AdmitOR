# IR: {"sets":{"F":"0,...,9","P":"0,...,8"},"params":{"a":"earliest landing times, ordered by F","b":"latest landing times, ordered by F"},"variables":{"t[F]":"continuous real","d":"continuous nonnegative"},"constraints":["a[j] <= t[j] <= b[j] for j in F","t[j+1] - t[j] >= d for j in P"],"objective":"maximize d"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Return the optimal separation; round the objective for nearest-time reporting."""
    a = params["a"]
    b = params["b"]

    if len(a) != 10 or len(b) != 10:
        return {"objective": None, "status": "invalid_dimensions"}

    model = pyo.ConcreteModel()
    model.flights = pyo.RangeSet(0, 9)
    model.adjacent_pairs = pyo.RangeSet(0, 8)

    model.earliest = pyo.Param(
        model.flights,
        initialize={j: a[j] for j in range(10)},
        within=pyo.Reals,
    )
    model.latest = pyo.Param(
        model.flights,
        initialize={j: b[j] for j in range(10)},
        within=pyo.Reals,
    )

    model.landing_time = pyo.Var(model.flights, domain=pyo.Reals)
    model.minimum_separation = pyo.Var(domain=pyo.NonNegativeReals)

    def window_rule(instance, j):
        return pyo.inequality(
            instance.earliest[j],
            instance.landing_time[j],
            instance.latest[j],
        )

    model.landing_windows = pyo.Constraint(
        model.flights, rule=window_rule
    )

    def separation_rule(instance, j):
        return (
            instance.landing_time[j + 1] - instance.landing_time[j]
            >= instance.minimum_separation
        )

    model.separation_limits = pyo.Constraint(
        model.adjacent_pairs, rule=separation_rule
    )

    model.separation_objective = pyo.Objective(
        expr=model.minimum_separation,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.separation_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}