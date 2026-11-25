# IR: {"sets":{"F":"{0,...,7}","E":"indices of params['conflict_edges']"},"params":{"d[f]":"params['durations'][f]","(i[e],j[e])":"params['conflict_edges'][e]","H":"sum(d[f] for f in F)"},"variables":{"s[f]":"continuous, 0 <= s[f] <= H-d[f]","C":"continuous, 0 <= C <= H","y[e]":"binary"},"constraints":["C >= s[f]+d[f] for every f in F","s[i[e]]+d[i[e]] <= s[j[e]]+H*(1-y[e]) for every e in E","s[j[e]]+d[j[e]] <= s[i[e]]+H*y[e] for every e in E"],"objective":"minimize C; each flight occupies [s[f],s[f]+d[f])"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    flights = range(8)
    durations = {
        flight: float(params["durations"][flight])
        for flight in flights
    }
    conflict_edges = [
        (int(pair[0]), int(pair[1]))
        for pair in params["conflict_edges"]
    ]
    horizon = sum(durations.values())

    model = pyo.ConcreteModel()
    model.flight_set = pyo.Set(initialize=flights, ordered=True)
    model.edge_set = pyo.Set(
        initialize=range(len(conflict_edges)), ordered=True
    )
    model.occupancy_duration = pyo.Param(
        model.flight_set,
        initialize=durations,
        within=pyo.NonNegativeReals,
    )

    def start_bounds(instance, flight):
        return (
            0,
            horizon - pyo.value(instance.occupancy_duration[flight]),
        )

    model.start_time = pyo.Var(
        model.flight_set,
        domain=pyo.NonNegativeReals,
        bounds=start_bounds,
    )
    model.schedule_end = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )
    model.precedes = pyo.Var(model.edge_set, domain=pyo.Binary)

    def completion_rule(instance, flight):
        return (
            instance.schedule_end
            >= instance.start_time[flight]
            + instance.occupancy_duration[flight]
        )

    model.completion_limits = pyo.Constraint(
        model.flight_set, rule=completion_rule
    )

    def forward_rule(instance, edge):
        first, second = conflict_edges[edge]
        return (
            instance.start_time[first]
            + instance.occupancy_duration[first]
            <= instance.start_time[second]
            + horizon * (1 - instance.precedes[edge])
        )

    model.forward_separation = pyo.Constraint(
        model.edge_set, rule=forward_rule
    )

    def reverse_rule(instance, edge):
        first, second = conflict_edges[edge]
        return (
            instance.start_time[second]
            + instance.occupancy_duration[second]
            <= instance.start_time[first]
            + horizon * instance.precedes[edge]
        )

    model.reverse_separation = pyo.Constraint(
        model.edge_set, rule=reverse_rule
    )
    model.schedule_objective = pyo.Objective(
        expr=model.schedule_end,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.schedule_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}