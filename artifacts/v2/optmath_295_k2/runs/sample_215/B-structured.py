# IR: {"sets":{"N":[0,1,2,3,4],"A":"ordered pairs (i,j) in N x N with i != j"},"params":{"weights":"real weights from params['weights']; accepts a 5x5 matrix, nested mapping, pair-keyed mapping, or row-major flat sequence of 20 off-diagonal or 25 full-matrix entries","num_facilities":"exact facility count from params['num_facilities']"},"variables":{"selected[i]":"binary for i in N","pair_active[i,j]":"binary for (i,j) in A"},"constraints":["sum(selected[i] for i in N) == num_facilities","pair_active[i,j] <= selected[i] for (i,j) in A","pair_active[i,j] <= selected[j] for (i,j) in A","pair_active[i,j] >= selected[i] + selected[j] - 1 for (i,j) in A"],"objective":"maximize sum(weights[i,j] * pair_active[i,j] for (i,j) in A)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    weights = params["weights"]
    num_facilities = params["num_facilities"]

    nodes = list(range(5))
    ordered_pairs = [
        (i, j)
        for i in nodes
        for j in nodes
        if i != j
    ]

    if isinstance(weights, Mapping):
        def get_weight(i, j):
            pair_keys = (
                (i, j),
                str((i, j)),
                f"({i},{j})",
                f"{i},{j}",
            )
            for key in pair_keys:
                if key in weights:
                    return weights[key]

            row = weights[i] if i in weights else weights[str(i)]
            if isinstance(row, Mapping):
                return row[j] if j in row else row[str(j)]
            return row[j]

        pair_weights = {
            (i, j): get_weight(i, j)
            for i, j in ordered_pairs
        }
    elif len(weights) == len(ordered_pairs):
        # Flat sequence: (0,1), (0,2), ..., (4,2), (4,3).
        pair_weights = {
            pair: weights[position]
            for position, pair in enumerate(ordered_pairs)
        }
    elif len(weights) == len(nodes) ** 2:
        # Flat full matrix in row-major order; diagonal entries are unused.
        pair_weights = {
            (i, j): weights[i * len(nodes) + j]
            for i, j in ordered_pairs
        }
    elif len(weights) == len(nodes):
        pair_weights = {
            (i, j): weights[i][j]
            for i, j in ordered_pairs
        }
    else:
        raise ValueError(
            "weights must be a 5x5 matrix, a nested or pair-keyed mapping, "
            "or a flat sequence containing 20 or 25 entries."
        )

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.ordered_pairs = pyo.Set(
        dimen=2,
        initialize=ordered_pairs,
        ordered=True,
    )

    model.pair_weights = pyo.Param(
        model.ordered_pairs,
        initialize=pair_weights,
        within=pyo.Reals,
    )
    model.required_facilities = pyo.Param(
        initialize=num_facilities,
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.nodes, domain=pyo.Binary)
    model.pair_active = pyo.Var(model.ordered_pairs, domain=pyo.Binary)

    model.facility_count = pyo.Constraint(
        expr=sum(model.selected[i] for i in model.nodes)
        == model.required_facilities
    )

    def first_endpoint_rule(instance, i, j):
        return instance.pair_active[i, j] <= instance.selected[i]

    def second_endpoint_rule(instance, i, j):
        return instance.pair_active[i, j] <= instance.selected[j]

    def both_endpoints_rule(instance, i, j):
        return (
            instance.pair_active[i, j]
            >= instance.selected[i] + instance.selected[j] - 1
        )

    model.first_endpoint = pyo.Constraint(
        model.ordered_pairs,
        rule=first_endpoint_rule,
    )
    model.second_endpoint = pyo.Constraint(
        model.ordered_pairs,
        rule=second_endpoint_rule,
    )
    model.both_endpoints = pyo.Constraint(
        model.ordered_pairs,
        rule=both_endpoints_rule,
    )

    model.total_dispersion = pyo.Objective(
        expr=sum(
            model.pair_weights[i, j] * model.pair_active[i, j]
            for i, j in model.ordered_pairs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_dispersion))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}