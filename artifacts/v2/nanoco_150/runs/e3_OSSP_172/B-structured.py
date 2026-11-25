# IR: {"sets":{"P":["P0","P1","P2"],"S":["S0","S1","S2"],"O":"P x S","D":"unordered distinct operation pairs (a,b) sharing a prototype or station"},"params":{"input":["duration_P0_S0","duration_P0_S1","duration_P0_S2","duration_P1_S0","duration_P1_S1","duration_P1_S2","duration_P2_S0","duration_P2_S1","duration_P2_S2"],"duration[p,s]":"corresponding nonnegative input duration","H":"sum(duration[p,s] for (p,s) in O)"},"variables":{"start[o]":{"type":"continuous","bounds":"[0,H-duration[o]]"},"before[a,b]":{"type":"binary","index":"D"},"makespan":{"type":"continuous","bounds":"[0,H]"}},"constraints":["start[o]+duration[o] <= makespan for o in O","start[a]+duration[a] <= start[b]+H*(1-before[a,b]) for (a,b) in D","start[b]+duration[b] <= start[a]+H*before[a,b] for (a,b) in D"],"objective":"minimize makespan"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    durations = {
        ("P0", "S0"): params["duration_P0_S0"],
        ("P0", "S1"): params["duration_P0_S1"],
        ("P0", "S2"): params["duration_P0_S2"],
        ("P1", "S0"): params["duration_P1_S0"],
        ("P1", "S1"): params["duration_P1_S1"],
        ("P1", "S2"): params["duration_P1_S2"],
        ("P2", "S0"): params["duration_P2_S0"],
        ("P2", "S1"): params["duration_P2_S1"],
        ("P2", "S2"): params["duration_P2_S2"],
    }

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=("P0", "P1", "P2"), ordered=True)
    model.S = pyo.Set(initialize=("S0", "S1", "S2"), ordered=True)
    model.O = pyo.Set(
        dimen=2,
        initialize=[(prototype, station)
                    for prototype in model.P
                    for station in model.S],
        ordered=True,
    )
    model.duration = pyo.Param(
        model.O,
        initialize=durations,
        within=pyo.NonNegativeReals,
    )

    horizon = sum(pyo.value(model.duration[operation]) for operation in model.O)
    model.H = pyo.Param(initialize=horizon, within=pyo.NonNegativeReals)

    conflict_pairs = [
        (first[0], first[1], second[0], second[1])
        for first, second in combinations(model.O, 2)
        if first[0] == second[0] or first[1] == second[1]
    ]
    model.D = pyo.Set(dimen=4, initialize=conflict_pairs, ordered=True)

    def start_bounds(instance, prototype, station):
        return (
            0,
            pyo.value(instance.H - instance.duration[prototype, station]),
        )

    model.start = pyo.Var(
        model.O,
        domain=pyo.NonNegativeReals,
        bounds=start_bounds,
    )
    model.before = pyo.Var(model.D, domain=pyo.Binary)
    model.makespan = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )

    def completion_rule(instance, prototype, station):
        return (
            instance.start[prototype, station]
            + instance.duration[prototype, station]
            <= instance.makespan
        )

    model.completion_limits = pyo.Constraint(model.O, rule=completion_rule)

    def first_before_second_rule(
        instance, first_prototype, first_station,
        second_prototype, second_station
    ):
        order = instance.before[
            first_prototype, first_station, second_prototype, second_station
        ]
        return (
            instance.start[first_prototype, first_station]
            + instance.duration[first_prototype, first_station]
            <= instance.start[second_prototype, second_station]
            + instance.H * (1 - order)
        )

    def second_before_first_rule(
        instance, first_prototype, first_station,
        second_prototype, second_station
    ):
        order = instance.before[
            first_prototype, first_station, second_prototype, second_station
        ]
        return (
            instance.start[second_prototype, second_station]
            + instance.duration[second_prototype, second_station]
            <= instance.start[first_prototype, first_station]
            + instance.H * order
        )

    model.forward_nonoverlap = pyo.Constraint(
        model.D, rule=first_before_second_rule
    )
    model.reverse_nonoverlap = pyo.Constraint(
        model.D, rule=second_before_first_rule
    )
    model.total_completion_time = pyo.Objective(
        expr=model.makespan,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_completion_time))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}