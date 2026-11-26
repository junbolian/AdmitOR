# IR: {"sets":{"F":"1..10","P":"1..9"},"params":{"a":"params['a'], ordered length-10 sequence","b":"params['b'], ordered length-10 sequence"},"variables":{"t[j]":"Real, j in F","gap":"NonNegativeReal"},"constraints":["a[j-1] <= t[j] <= b[j-1], j in F","t[j+1] - t[j] >= gap, j in P"],"objective":"maximize gap"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    a = params["a"]
    b = params["b"]

    model = pyo.ConcreteModel()
    model.flights = pyo.RangeSet(1, 10)
    model.adjacent_pairs = pyo.RangeSet(1, 9)

    model.earliest = pyo.Param(
        model.flights,
        initialize=lambda mdl, j: a[j - 1],
        within=pyo.Reals,
    )
    model.latest = pyo.Param(
        model.flights,
        initialize=lambda mdl, j: b[j - 1],
        within=pyo.Reals,
    )

    model.landing_time = pyo.Var(model.flights, domain=pyo.Reals)
    model.gap = pyo.Var(domain=pyo.NonNegativeReals)

    model.landing_windows = pyo.Constraint(
        model.flights,
        rule=lambda mdl, j: pyo.inequality(
            mdl.earliest[j], mdl.landing_time[j], mdl.latest[j]
        ),
    )
    model.minimum_separations = pyo.Constraint(
        model.adjacent_pairs,
        rule=lambda mdl, j: (
            mdl.landing_time[j + 1] - mdl.landing_time[j] >= mdl.gap
        ),
    )
    model.separation_objective = pyo.Objective(
        expr=model.gap,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.separation_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    # Preserve the optimal objective; round this value for nearest-time reporting.
    return {"objective": obj_val, "status": "optimal"}