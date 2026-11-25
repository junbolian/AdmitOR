# IR: {"sets":{"N":[0,1,2,3,4],"A":"{(i,j): i,j in N, i!=j}","P":"{(i,j): i,j in N, i<j}"},"params":{"distances":"Directed distances on A from params['distances']; accepts pair-keyed mappings, nested rows, or flat row-major arrays of 20 off-diagonal or 25 matrix entries; unordered pairs use the i<j entry"},"variables":{"selected[i]":"binary, i in N","paired[i,j]":"binary, (i,j) in P"},"constraints":["sum(selected[i] for i in N)==3","paired[i,j]<=selected[i] for (i,j) in P","paired[i,j]<=selected[j] for (i,j) in P","paired[i,j]>=selected[i]+selected[j]-1 for (i,j) in P"],"objective":"maximize sum(distances[i,j]*paired[i,j] for (i,j) in P)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed_value(values, position):
    if isinstance(values, Mapping):
        if position in values:
            return values[position]
        return values[str(position)]
    return values[position]


def _distance_value(distances, i, j):
    if isinstance(distances, Mapping):
        for key in (
            (i, j),
            f"{i},{j}",
            f"{i}, {j}",
            f"({i},{j})",
            f"({i}, {j})",
            f"[{i},{j}]",
            f"[{i}, {j}]",
        ):
            if key in distances:
                return distances[key]

    if len(distances) == 20:
        # Row-major directed pairs, omitting diagonal entries.
        position = i * 4 + (j if j < i else j - 1)
        return _indexed_value(distances, position)

    if len(distances) == 25:
        # Row-major flattened 5-by-5 matrix, including its diagonal.
        return _indexed_value(distances, i * 5 + j)

    row = _indexed_value(distances, i)
    return _indexed_value(row, j)


def solve(params):
    distances = params["distances"]

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 4)

    model.directed_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.nodes
            for j in model.nodes
            if i != j
        ],
    )
    model.unordered_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.nodes
            for j in model.nodes
            if i < j
        ],
    )

    model.distance_data = pyo.Param(
        model.directed_pairs,
        initialize={
            (i, j): _distance_value(distances, i, j)
            for i, j in model.directed_pairs
        },
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.nodes, domain=pyo.Binary)
    model.paired = pyo.Var(model.unordered_pairs, domain=pyo.Binary)

    model.selection_count = pyo.Constraint(
        expr=sum(model.selected[i] for i in model.nodes) == 3
    )
    model.pair_first_selected = pyo.Constraint(
        model.unordered_pairs,
        rule=lambda mdl, i, j: mdl.paired[i, j] <= mdl.selected[i],
    )
    model.pair_second_selected = pyo.Constraint(
        model.unordered_pairs,
        rule=lambda mdl, i, j: mdl.paired[i, j] <= mdl.selected[j],
    )
    model.pair_both_selected = pyo.Constraint(
        model.unordered_pairs,
        rule=lambda mdl, i, j: (
            mdl.paired[i, j] >= mdl.selected[i] + mdl.selected[j] - 1
        ),
    )

    model.dispersion_objective = pyo.Objective(
        expr=sum(
            model.distance_data[i, j] * model.paired[i, j]
            for i, j in model.unordered_pairs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # Solution loading can fail for infeasible models. Success is
        # determined solely by whether the objective can be evaluated.
        pass

    try:
        obj_val = float(pyo.value(model.dispersion_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}