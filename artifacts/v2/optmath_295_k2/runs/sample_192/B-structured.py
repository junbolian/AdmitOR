# IR: {"sets":{"A":[0,1,2,3],"P":"all permutations of A","K":[0,1,2],"D":"directed pairs in the order specified in the question"},"params":{"earliest":"A -> real","latest":"A -> real","target":"A -> real","early_penalty":"A -> nonnegative real","late_penalty":"A -> nonnegative real","separation":"D -> nonnegative real","M[i,j]":"max(0,latest[i]+separation[i,j]-earliest[j])"},"variables":{"landing[i]":"real in [earliest[i],latest[i]]","early[i]":"nonnegative real","late[i]":"nonnegative real","choose[p]":"binary"},"constraints":["sum(p in P) choose[p] = 1","early[i] >= target[i]-landing[i] for i in A","late[i] >= landing[i]-target[i] for i in A","landing[p[k+1]] >= landing[p[k]]+separation[p[k],p[k+1]]-M[p[k],p[k+1]]*(1-choose[p]) for p in P,k in K"],"objective":"minimize sum(i in A) early_penalty[i]*early[i]+late_penalty[i]*late[i]"}
from collections.abc import Mapping
from itertools import permutations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Schedule four aircraft, enforcing separation between consecutive landings.

    Aircraft parameters accept lists or dictionaries keyed by aircraft index.
    Separation accepts a flat list in the specified pair order, a 4-by-4
    nested container, or a dictionary keyed by (i, j), "i,j", or "i<j".
    """
    aircraft = tuple(range(4))
    directed_pairs = (
        (0, 1), (1, 0),
        (0, 2), (2, 0),
        (0, 3), (3, 0),
        (1, 2), (2, 1),
        (1, 3), (3, 1),
        (2, 3), (3, 2),
    )
    sequences = tuple(permutations(aircraft))

    def indexed(container, key):
        if isinstance(container, Mapping):
            if key in container:
                return container[key]
            return container[str(key)]
        return container[key]

    earliest_input = params["earliest"]
    latest_input = params["latest"]
    target_input = params["target"]
    early_penalty_input = params["early_penalty"]
    late_penalty_input = params["late_penalty"]
    separation_input = params["separation"]

    earliest = {i: float(indexed(earliest_input, i)) for i in aircraft}
    latest = {i: float(indexed(latest_input, i)) for i in aircraft}
    target = {i: float(indexed(target_input, i)) for i in aircraft}
    early_penalty = {
        i: float(indexed(early_penalty_input, i)) for i in aircraft
    }
    late_penalty = {
        i: float(indexed(late_penalty_input, i)) for i in aircraft
    }

    def separation_value(i, j, position):
        if isinstance(separation_input, Mapping):
            for key in ((i, j), f"{i},{j}", f"{i}<{j}"):
                if key in separation_input:
                    return float(separation_input[key])
            return float(indexed(indexed(separation_input, i), j))
        if len(separation_input) == len(directed_pairs):
            return float(separation_input[position])
        return float(indexed(indexed(separation_input, i), j))

    separation = {
        (i, j): separation_value(i, j, position)
        for position, (i, j) in enumerate(directed_pairs)
    }

    if any(earliest[i] > latest[i] for i in aircraft):
        return {"objective": None, "status": "invalid_window"}

    big_m = {
        (i, j): max(0.0, latest[i] + separation[i, j] - earliest[j])
        for i, j in directed_pairs
    }

    model = pyo.ConcreteModel()
    model.aircraft = pyo.Set(initialize=aircraft, ordered=True)
    model.sequence_ids = pyo.RangeSet(0, len(sequences) - 1)
    model.adjacency_steps = pyo.RangeSet(0, len(aircraft) - 2)
    model.directed_pairs = pyo.Set(
        initialize=directed_pairs, dimen=2, ordered=True
    )

    model.earliest = pyo.Param(model.aircraft, initialize=earliest)
    model.latest = pyo.Param(model.aircraft, initialize=latest)
    model.target = pyo.Param(model.aircraft, initialize=target)
    model.early_penalty = pyo.Param(
        model.aircraft, initialize=early_penalty, within=pyo.NonNegativeReals
    )
    model.late_penalty = pyo.Param(
        model.aircraft, initialize=late_penalty, within=pyo.NonNegativeReals
    )
    model.separation = pyo.Param(
        model.directed_pairs,
        initialize=separation,
        within=pyo.NonNegativeReals,
    )
    model.big_m = pyo.Param(
        model.directed_pairs, initialize=big_m, within=pyo.NonNegativeReals
    )

    model.landing = pyo.Var(
        model.aircraft,
        domain=pyo.Reals,
        bounds=lambda instance, i: (
            pyo.value(instance.earliest[i]),
            pyo.value(instance.latest[i]),
        ),
    )
    model.early = pyo.Var(model.aircraft, domain=pyo.NonNegativeReals)
    model.late = pyo.Var(model.aircraft, domain=pyo.NonNegativeReals)
    model.choose = pyo.Var(model.sequence_ids, domain=pyo.Binary)

    model.one_sequence = pyo.Constraint(
        expr=sum(model.choose[s] for s in model.sequence_ids) == 1
    )
    model.early_deviation = pyo.Constraint(
        model.aircraft,
        rule=lambda instance, i: (
            instance.early[i] >= instance.target[i] - instance.landing[i]
        ),
    )
    model.late_deviation = pyo.Constraint(
        model.aircraft,
        rule=lambda instance, i: (
            instance.late[i] >= instance.landing[i] - instance.target[i]
        ),
    )

    def consecutive_separation_rule(instance, sequence_id, step):
        sequence = sequences[sequence_id]
        predecessor = sequence[step]
        successor = sequence[step + 1]
        return (
            instance.landing[successor]
            >= instance.landing[predecessor]
            + instance.separation[predecessor, successor]
            - instance.big_m[predecessor, successor]
            * (1 - instance.choose[sequence_id])
        )

    model.consecutive_separation = pyo.Constraint(
        model.sequence_ids,
        model.adjacency_steps,
        rule=consecutive_separation_rule,
    )
    model.total_penalty = pyo.Objective(
        expr=sum(
            model.early_penalty[i] * model.early[i]
            + model.late_penalty[i] * model.late[i]
            for i in model.aircraft
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_penalty))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}