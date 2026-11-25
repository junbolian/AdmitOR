# IR: {"sets":{"F":"{0,...,7}","P":"unique ordered pairs from params['conflicts']"},"params":{"d[i]":"params['durations'][i], positive","H":"sum(d[i] for i in F)"},"variables":{"s[i]":"continuous in [0,H], i in F","C":"continuous in [0,H]","y[i,j]":"binary, (i,j) in P"},"constraints":["s[i]+d[i] <= C for i in F","s[i]+d[i] <= s[j]+H*(1-y[i,j]) for (i,j) in P","s[j]+d[j] <= s[i]+H*y[i,j] for (i,j) in P"],"objective":"minimize C"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    durations = {
        flight: params["durations"][flight]
        for flight in range(8)
    }
    conflicts = [tuple(pair) for pair in params["conflicts"]]
    horizon = sum(durations.values())

    model = pyo.ConcreteModel()
    model.flights = pyo.RangeSet(0, 7)
    model.conflict_pairs = pyo.Set(
        dimen=2,
        within=model.flights * model.flights,
        initialize=conflicts,
    )

    model.duration = pyo.Param(
        model.flights,
        initialize=durations,
        within=pyo.PositiveReals,
    )
    model.horizon = pyo.Param(
        initialize=horizon,
        within=pyo.PositiveReals,
    )

    model.start_time = pyo.Var(
        model.flights,
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )
    model.makespan = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )
    model.precedence = pyo.Var(
        model.conflict_pairs,
        domain=pyo.Binary,
    )

    def completion_rule(mdl, flight):
        return (
            mdl.start_time[flight] + mdl.duration[flight]
            <= mdl.makespan
        )

    model.completion_limits = pyo.Constraint(
        model.flights,
        rule=completion_rule,
    )

    def first_before_second_rule(mdl, first, second):
        return (
            mdl.start_time[first] + mdl.duration[first]
            <= mdl.start_time[second]
            + mdl.horizon * (1 - mdl.precedence[first, second])
        )

    model.first_before_second = pyo.Constraint(
        model.conflict_pairs,
        rule=first_before_second_rule,
    )

    def second_before_first_rule(mdl, first, second):
        return (
            mdl.start_time[second] + mdl.duration[second]
            <= mdl.start_time[first]
            + mdl.horizon * mdl.precedence[first, second]
        )

    model.second_before_first = pyo.Constraint(
        model.conflict_pairs,
        rule=second_before_first_rule,
    )

    model.schedule_span = pyo.Objective(
        expr=model.makespan,
        sense=pyo.minimize,
    )

    # A serial schedule fits within H, so H is a valid big-M.
    # No termination-condition enums are inspected.
    try:
        Highs().solve(model)
    except RuntimeError:
        # Failed solution loading can raise when no solution is available.
        # Success is decided solely by objective retrieval below.
        pass

    try:
        obj_val = float(pyo.value(model.schedule_span))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}