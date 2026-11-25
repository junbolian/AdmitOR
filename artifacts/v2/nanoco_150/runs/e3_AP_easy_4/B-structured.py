# IR: {"sets":{"arms":[0,1,2,3,4],"stations":[0,1,2,3,4]},"params":{"cycle_time":{"source":"params['cycle_time']","shape":[5,5],"type":"nonnegative_real"}},"variables":{"assigned[arm,station]":{"type":"binary"}},"constraints":["For each arm: sum(assigned[arm,station] for station in stations) = 1.","For each station: sum(assigned[arm,station] for arm in arms) = 1."],"objective":{"sense":"minimize","expression":"sum(cycle_time[arm,station] * assigned[arm,station] for arm in arms for station in stations)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cycle_time = params["cycle_time"]

    model = pyo.ConcreteModel()
    model.arms = pyo.RangeSet(0, 4)
    model.stations = pyo.RangeSet(0, 4)

    model.cycle_time = pyo.Param(
        model.arms,
        model.stations,
        initialize=lambda _, arm, station: cycle_time[arm][station],
        within=pyo.NonNegativeReals,
    )

    model.assigned = pyo.Var(
        model.arms,
        model.stations,
        domain=pyo.Binary,
    )

    def arm_assignment_rule(instance, arm):
        return sum(
            instance.assigned[arm, station]
            for station in instance.stations
        ) == 1

    model.arm_assignment = pyo.Constraint(
        model.arms,
        rule=arm_assignment_rule,
    )

    def station_assignment_rule(instance, station):
        return sum(
            instance.assigned[arm, station]
            for arm in instance.arms
        ) == 1

    model.station_assignment = pyo.Constraint(
        model.stations,
        rule=station_assignment_rule,
    )

    model.total_cycle_time = pyo.Objective(
        expr=sum(
            model.cycle_time[arm, station] * model.assigned[arm, station]
            for arm in model.arms
            for station in model.stations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cycle_time))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}