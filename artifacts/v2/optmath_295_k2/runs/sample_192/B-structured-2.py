# IR: {"sets":{"A":[0,1,2,3],"P":"ordered pairs (i,j) with i != j"},"params":{"earliest":"params['earliest'][i]","latest":"params['latest'][i]","target":"params['target'][i]","early_penalty":"params['early_penalty'][i]","late_penalty":"params['late_penalty'][i]","separation":"params['separation'], normalized to ordered pairs","big_m":"max(0, latest[i] + separation[i,j] - earliest[j])"},"variables":{"landing[i]":"continuous, earliest[i] <= landing[i] <= latest[i]","early[i]":"nonnegative continuous","late[i]":"nonnegative continuous","follows[i,j]":"binary; j immediately follows i","first[i]":"binary","last[i]":"binary","rank[i]":"continuous in [0, |A|-1]"},"constraints":["landing[i] - target[i] = late[i] - early[i]","sum(j != i, follows[j,i]) + first[i] = 1","sum(j != i, follows[i,j]) + last[i] = 1","sum(i, first[i]) = 1","sum(i, last[i]) = 1","rank[j] >= rank[i] + 1 - |A|*(1-follows[i,j])","landing[j] >= landing[i] + separation[i,j] - big_m[i,j]*(1-follows[i,j])"],"objective":"minimize sum(i, early_penalty[i]*early[i] + late_penalty[i]*late[i])"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    aircraft = range(4)
    ordered_pairs = [
        (left, right)
        for left in aircraft
        for right in aircraft
        if left != right
    ]

    earliest = params["earliest"]
    latest = params["latest"]
    target = params["target"]
    early_penalty = params["early_penalty"]
    late_penalty = params["late_penalty"]
    separation_input = params["separation"]

    # A flat separation sequence uses the order specified in the problem.
    flat_pair_order = [
        (0, 1), (1, 0),
        (0, 2), (2, 0),
        (0, 3), (3, 0),
        (1, 2), (2, 1),
        (1, 3), (3, 1),
        (2, 3), (3, 2),
    ]

    # Also accept a tuple-keyed mapping or a nested 4-by-4 structure.
    if isinstance(separation_input, Mapping):
        if all(pair in separation_input for pair in ordered_pairs):
            separation = {
                pair: separation_input[pair]
                for pair in ordered_pairs
            }
        else:
            separation = {
                (left, right): separation_input[left][right]
                for left, right in ordered_pairs
            }
    elif len(separation_input) == len(flat_pair_order):
        separation = dict(zip(flat_pair_order, separation_input))
    else:
        separation = {
            (left, right): separation_input[left][right]
            for left, right in ordered_pairs
        }

    model = pyo.ConcreteModel()
    model.A = pyo.Set(initialize=aircraft, ordered=True)
    model.P = pyo.Set(initialize=ordered_pairs, dimen=2, ordered=True)

    model.earliest = pyo.Param(
        model.A, initialize=lambda mdl, idx: earliest[idx]
    )
    model.latest = pyo.Param(
        model.A, initialize=lambda mdl, idx: latest[idx]
    )
    model.target = pyo.Param(
        model.A, initialize=lambda mdl, idx: target[idx]
    )
    model.early_penalty = pyo.Param(
        model.A, initialize=lambda mdl, idx: early_penalty[idx]
    )
    model.late_penalty = pyo.Param(
        model.A, initialize=lambda mdl, idx: late_penalty[idx]
    )
    model.separation = pyo.Param(model.P, initialize=separation)
    model.big_m = pyo.Param(
        model.P,
        initialize=lambda mdl, left, right: max(
            0,
            pyo.value(
                mdl.latest[left]
                + mdl.separation[left, right]
                - mdl.earliest[right]
            ),
        ),
    )

    model.landing = pyo.Var(
        model.A,
        domain=pyo.Reals,
        bounds=lambda mdl, idx: (
            mdl.earliest[idx],
            mdl.latest[idx],
        ),
    )
    model.early = pyo.Var(model.A, domain=pyo.NonNegativeReals)
    model.late = pyo.Var(model.A, domain=pyo.NonNegativeReals)
    model.follows = pyo.Var(model.P, domain=pyo.Binary)
    model.first = pyo.Var(model.A, domain=pyo.Binary)
    model.last = pyo.Var(model.A, domain=pyo.Binary)
    model.rank = pyo.Var(
        model.A,
        domain=pyo.NonNegativeReals,
        bounds=(0, len(aircraft) - 1),
    )

    model.deviation_balance = pyo.Constraint(
        model.A,
        rule=lambda mdl, idx: (
            mdl.landing[idx] - mdl.target[idx]
            == mdl.late[idx] - mdl.early[idx]
        ),
    )

    model.predecessor_requirement = pyo.Constraint(
        model.A,
        rule=lambda mdl, idx: (
            sum(
                mdl.follows[other, idx]
                for other in mdl.A
                if other != idx
            )
            + mdl.first[idx]
            == 1
        ),
    )

    model.successor_requirement = pyo.Constraint(
        model.A,
        rule=lambda mdl, idx: (
            sum(
                mdl.follows[idx, other]
                for other in mdl.A
                if other != idx
            )
            + mdl.last[idx]
            == 1
        ),
    )

    model.single_first = pyo.Constraint(
        expr=sum(model.first[idx] for idx in model.A) == 1
    )
    model.single_last = pyo.Constraint(
        expr=sum(model.last[idx] for idx in model.A) == 1
    )

    # Eliminate cycles so that selected adjacency arcs form one landing path.
    model.sequence_order = pyo.Constraint(
        model.P,
        rule=lambda mdl, left, right: (
            mdl.rank[right]
            >= mdl.rank[left] + 1
            - len(aircraft) * (1 - mdl.follows[left, right])
        ),
    )

    model.adjacent_separation = pyo.Constraint(
        model.P,
        rule=lambda mdl, left, right: (
            mdl.landing[right]
            >= mdl.landing[left] + mdl.separation[left, right]
            - mdl.big_m[left, right] * (1 - mdl.follows[left, right])
        ),
    )

    model.total_penalty = pyo.Objective(
        expr=sum(
            model.early_penalty[idx] * model.early[idx]
            + model.late_penalty[idx] * model.late[idx]
            for idx in model.A
        ),
        sense=pyo.minimize,
    )

    # APPsi can raise RuntimeError when no feasible solution can be loaded.
    # Success is determined exclusively by retrieving the objective below.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_penalty))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}