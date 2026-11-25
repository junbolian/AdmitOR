# IR: {"sets":{"I":[0,1,2,3,4],"P":"{(i,j): i,j in I, i<j}"},"params":{"earliest":"I -> real, from params","latest":"I -> real, from params","target":"I -> real, from params","early_cost":"I -> nonnegative real, from params","late_cost":"I -> nonnegative real, from params","separation":"P -> nonnegative real, from params","M_forward":"max(0,latest[i]+separation[i,j]-earliest[j])","M_reverse":"max(0,latest[j]+separation[i,j]-earliest[i])"},"variables":{"landing":"I -> real, earliest[i]<=landing[i]<=latest[i]","early":"I -> nonnegative real","late":"I -> nonnegative real","before":"P -> binary; 1 means i lands before j"},"constraints":["landing[i]-target[i]=late[i]-early[i] for i in I","landing[j]>=landing[i]+separation[i,j]-M_forward[i,j]*(1-before[i,j]) for (i,j) in P","landing[i]>=landing[j]+separation[i,j]-M_reverse[i,j]*before[i,j] for (i,j) in P"],"objective":"minimize sum(early_cost[i]*early[i]+late_cost[i]*late[i] for i in I)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the five-aircraft landing problem using Pyomo and HiGHS."""
    aircraft = range(5)
    pairs = [(i, j) for i in aircraft for j in aircraft if i < j]

    earliest_data = params["earliest"]
    latest_data = params["latest"]
    target_data = params["target"]
    early_cost_data = params["early_cost"]
    late_cost_data = params["late_cost"]
    separation_data = params["separation"]

    def indexed_value(data, i):
        if isinstance(data, Mapping):
            return data[i] if i in data else data[str(i)]
        return data[i]

    def separation_value(i, j, position):
        # Accept pair-keyed mappings, nested mappings, flat vectors in
        # the stated pair order, or five-by-five matrices.
        if isinstance(separation_data, Mapping):
            for key in ((i, j), str((i, j)), f"({i},{j})", f"{i},{j}"):
                if key in separation_data:
                    return separation_data[key]
            return indexed_value(indexed_value(separation_data, i), j)
        if len(separation_data) == len(pairs):
            return separation_data[position]
        return separation_data[i][j]

    model = pyo.ConcreteModel()
    model.I = pyo.Set(initialize=aircraft, ordered=True)
    model.P = pyo.Set(initialize=pairs, dimen=2, ordered=True)

    model.earliest = pyo.Param(
        model.I,
        initialize={i: indexed_value(earliest_data, i) for i in aircraft},
        within=pyo.Reals,
    )
    model.latest = pyo.Param(
        model.I,
        initialize={i: indexed_value(latest_data, i) for i in aircraft},
        within=pyo.Reals,
    )
    model.target = pyo.Param(
        model.I,
        initialize={i: indexed_value(target_data, i) for i in aircraft},
        within=pyo.Reals,
    )
    model.early_cost = pyo.Param(
        model.I,
        initialize={i: indexed_value(early_cost_data, i) for i in aircraft},
        within=pyo.NonNegativeReals,
    )
    model.late_cost = pyo.Param(
        model.I,
        initialize={i: indexed_value(late_cost_data, i) for i in aircraft},
        within=pyo.NonNegativeReals,
    )
    model.separation = pyo.Param(
        model.P,
        initialize={
            (i, j): separation_value(i, j, position)
            for position, (i, j) in enumerate(pairs)
        },
        within=pyo.NonNegativeReals,
    )

    model.M_forward = pyo.Param(
        model.P,
        initialize=lambda mdl, i, j: max(
            0,
            pyo.value(mdl.latest[i] + mdl.separation[i, j] - mdl.earliest[j]),
        ),
    )
    model.M_reverse = pyo.Param(
        model.P,
        initialize=lambda mdl, i, j: max(
            0,
            pyo.value(mdl.latest[j] + mdl.separation[i, j] - mdl.earliest[i]),
        ),
    )

    model.landing = pyo.Var(
        model.I,
        domain=pyo.Reals,
        bounds=lambda mdl, i: (mdl.earliest[i], mdl.latest[i]),
    )
    model.early = pyo.Var(model.I, domain=pyo.NonNegativeReals)
    model.late = pyo.Var(model.I, domain=pyo.NonNegativeReals)
    model.before = pyo.Var(model.P, domain=pyo.Binary)

    model.deviation_balance = pyo.Constraint(
        model.I,
        rule=lambda mdl, i: (
            mdl.landing[i] - mdl.target[i] == mdl.late[i] - mdl.early[i]
        ),
    )
    model.forward_separation = pyo.Constraint(
        model.P,
        rule=lambda mdl, i, j: (
            mdl.landing[j]
            >= mdl.landing[i]
            + mdl.separation[i, j]
            - mdl.M_forward[i, j] * (1 - mdl.before[i, j])
        ),
    )
    model.reverse_separation = pyo.Constraint(
        model.P,
        rule=lambda mdl, i, j: (
            mdl.landing[i]
            >= mdl.landing[j]
            + mdl.separation[i, j]
            - mdl.M_reverse[i, j] * mdl.before[i, j]
        ),
    )
    model.total_penalty = pyo.Objective(
        expr=sum(
            model.early_cost[i] * model.early[i]
            + model.late_cost[i] * model.late[i]
            for i in model.I
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPSI raises this when automatic solution loading finds no
        # feasible solution. Leave success determination to pyo.value.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_penalty))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}