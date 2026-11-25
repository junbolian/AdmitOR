# IR: {"sets":{"F":"0..7","E":"params['conflict_edges']"},"params":{"d":"params['durations'], indexed by F","H":"sum(d[i] for i in F)"},"variables":{"start[i]":"continuous, 0 <= start[i] <= H","span":"continuous, 0 <= span <= H","order[i,j]":"binary for (i,j) in E"},"constraints":["start[i] + d[i] <= span for i in F","start[i] + d[i] <= start[j] + H*(1-order[i,j]) for (i,j) in E","start[j] + d[j] <= start[i] + H*order[i,j] for (i,j) in E"],"objective":"minimize span"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    durations = params["durations"]
    conflict_edges = params["conflict_edges"]

    flights = range(8)
    horizon = sum(durations[flight] for flight in flights)

    model = pyo.ConcreteModel()

    model.flights = pyo.Set(initialize=flights, ordered=True)
    model.conflicts = pyo.Set(
        dimen=2,
        initialize=[tuple(edge) for edge in conflict_edges],
        within=model.flights * model.flights,
    )

    model.duration = pyo.Param(
        model.flights,
        initialize={flight: durations[flight] for flight in flights},
        within=pyo.PositiveReals,
    )
    model.horizon = pyo.Param(initialize=horizon, within=pyo.PositiveReals)

    model.start = pyo.Var(
        model.flights,
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )
    model.span = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )
    model.order = pyo.Var(model.conflicts, domain=pyo.Binary)

    def completion_rule(instance, flight):
        return (
            instance.start[flight] + instance.duration[flight]
            <= instance.span
        )

    model.completion_limits = pyo.Constraint(
        model.flights, rule=completion_rule
    )

    def first_before_second_rule(instance, first, second):
        return (
            instance.start[first] + instance.duration[first]
            <= instance.start[second]
            + instance.horizon * (1 - instance.order[first, second])
        )

    model.first_before_second = pyo.Constraint(
        model.conflicts, rule=first_before_second_rule
    )

    def second_before_first_rule(instance, first, second):
        return (
            instance.start[second] + instance.duration[second]
            <= instance.start[first]
            + instance.horizon * instance.order[first, second]
        )

    model.second_before_first = pyo.Constraint(
        model.conflicts, rule=second_before_first_rule
    )

    model.schedule_objective = pyo.Objective(
        expr=model.span,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.schedule_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}