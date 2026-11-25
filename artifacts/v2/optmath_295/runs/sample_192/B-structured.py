# IR: {"sets":{"A":[0,1,2,3],"Q":"all permutations of A","K":[0,1,2],"P":"ordered distinct pairs from A"},"params":{"early_penalty":"A -> nonnegative real","late_penalty":"A -> nonnegative real","earliest_landing":"A -> real","latest_landing":"A -> real","target_landing":"A -> real","separation_i_before_j":"P -> positive real"},"derived":{"M[i,j]":"max(0,latest_landing[i]+separation_i_before_j[i,j]-earliest_landing[j])"},"variables":{"landing[i]":"real in [earliest_landing[i],latest_landing[i]]","early[i]":"nonnegative real","late[i]":"nonnegative real","chosen[q]":"binary"},"constraints":["sum(q in Q) chosen[q] = 1","landing[i]-target_landing[i] = late[i]-early[i] for i in A","landing[q[k+1]] >= landing[q[k]]+separation_i_before_j[q[k],q[k+1]]-M[q[k],q[k+1]]*(1-chosen[q]) for q in Q,k in K"],"objective":"minimize sum(i in A) early_penalty[i]*early[i]+late_penalty[i]*late[i]","failure_handling":"Return missing_parameter if a required parameter is absent; after solving, determine success solely by objective retrieval."}

from collections.abc import Mapping
from itertools import permutations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Schedule four aircraft using separations between consecutive landings.

    Aircraft parameters accept sequences or mappings with integer aircraft keys.
    Separations accept a nested sequence/mapping or a mapping keyed by (i, j).
    Missing required inputs produce a failure result rather than invented data.
    """
    try:
        early_rates = params["early_penalty"]
        late_rates = params["late_penalty"]
        earliest = params["earliest_landing"]
        latest = params["latest_landing"]
        targets = params["target_landing"]
        separations = params["separation_i_before_j"]
    except KeyError as exc:
        return {
            "objective": None,
            "status": "missing_parameter:" + str(exc.args[0]),
        }

    aircraft = tuple(range(4))
    sequences = tuple(permutations(aircraft))
    ordered_pairs = tuple(
        (first, second)
        for first in aircraft
        for second in aircraft
        if first != second
    )

    def separation_value(first, second):
        if isinstance(separations, Mapping) and (first, second) in separations:
            return separations[first, second]
        return separations[first][second]

    model = pyo.ConcreteModel()

    model.aircraft = pyo.Set(initialize=aircraft, ordered=True)
    model.sequence_ids = pyo.Set(
        initialize=range(len(sequences)), ordered=True
    )
    model.adjacent_positions = pyo.Set(
        initialize=range(3), ordered=True
    )
    model.ordered_pairs = pyo.Set(
        initialize=ordered_pairs, dimen=2
    )

    model.early_penalty = pyo.Param(
        model.aircraft,
        initialize={idx: early_rates[idx] for idx in aircraft},
        within=pyo.NonNegativeReals,
    )
    model.late_penalty = pyo.Param(
        model.aircraft,
        initialize={idx: late_rates[idx] for idx in aircraft},
        within=pyo.NonNegativeReals,
    )
    model.earliest_landing = pyo.Param(
        model.aircraft,
        initialize={idx: earliest[idx] for idx in aircraft},
        within=pyo.Reals,
    )
    model.latest_landing = pyo.Param(
        model.aircraft,
        initialize={idx: latest[idx] for idx in aircraft},
        within=pyo.Reals,
    )
    model.target_landing = pyo.Param(
        model.aircraft,
        initialize={idx: targets[idx] for idx in aircraft},
        within=pyo.Reals,
    )
    model.separation = pyo.Param(
        model.ordered_pairs,
        initialize={
            (first, second): separation_value(first, second)
            for first, second in ordered_pairs
        },
        within=pyo.PositiveReals,
    )

    def big_m_rule(mdl, first, second):
        return max(
            0,
            pyo.value(
                mdl.latest_landing[first]
                + mdl.separation[first, second]
                - mdl.earliest_landing[second]
            ),
        )

    model.big_m = pyo.Param(
        model.ordered_pairs,
        initialize=big_m_rule,
        within=pyo.NonNegativeReals,
    )

    def landing_bounds(mdl, idx):
        return (
            pyo.value(mdl.earliest_landing[idx]),
            pyo.value(mdl.latest_landing[idx]),
        )

    model.landing = pyo.Var(
        model.aircraft,
        domain=pyo.Reals,
        bounds=landing_bounds,
    )
    model.early = pyo.Var(
        model.aircraft, domain=pyo.NonNegativeReals
    )
    model.late = pyo.Var(
        model.aircraft, domain=pyo.NonNegativeReals
    )
    model.chosen = pyo.Var(
        model.sequence_ids, domain=pyo.Binary
    )

    model.choose_sequence = pyo.Constraint(
        expr=sum(
            model.chosen[seq_id]
            for seq_id in model.sequence_ids
        ) == 1
    )

    def deviation_rule(mdl, idx):
        return (
            mdl.landing[idx] - mdl.target_landing[idx]
            == mdl.late[idx] - mdl.early[idx]
        )

    model.deviation_balance = pyo.Constraint(
        model.aircraft, rule=deviation_rule
    )

    def consecutive_separation_rule(mdl, seq_id, position):
        first = sequences[seq_id][position]
        second = sequences[seq_id][position + 1]
        return (
            mdl.landing[second]
            >= mdl.landing[first]
            + mdl.separation[first, second]
            - mdl.big_m[first, second] * (1 - mdl.chosen[seq_id])
        )

    model.consecutive_separation = pyo.Constraint(
        model.sequence_ids,
        model.adjacent_positions,
        rule=consecutive_separation_rule,
    )

    model.total_penalty = pyo.Objective(
        expr=sum(
            model.early_penalty[idx] * model.early[idx]
            + model.late_penalty[idx] * model.late[idx]
            for idx in model.aircraft
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # An infeasible solve may raise when automatic solution loading fails.
        # Objective retrieval below is the sole test for success.
        pass

    try:
        obj_val = float(pyo.value(model.total_penalty))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}