# IR: {"sets":{"N":[0,1,2,3,4],"A":"[(i,j) for i in N for j in N if i != j], in row-major order"},"params":{"weights":"params['weights']; nested matrix, ordered-pair mapping, flat 20-entry off-diagonal array, or flat 25-entry matrix","num_facilities":"params['num_facilities']"},"variables":{"selected[i]":"binary for i in N","pair_active[i,j]":"binary for (i,j) in A"},"constraints":["sum(selected[i] for i in N) == num_facilities","pair_active[i,j] <= selected[i] for (i,j) in A","pair_active[i,j] <= selected[j] for (i,j) in A","pair_active[i,j] >= selected[i] + selected[j] - 1 for (i,j) in A"],"objective":"maximize sum(weights[i,j] * pair_active[i,j] for (i,j) in A)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    weights = params["weights"]
    num_facilities = params["num_facilities"]

    nodes = list(range(5))
    ordered_pairs = [
        (i, j) for i in nodes for j in nodes if i != j
    ]
    pair_positions = {
        pair: position for position, pair in enumerate(ordered_pairs)
    }

    def read_weight(i, j):
        if isinstance(weights, Mapping):
            pair_keys = (
                (i, j),
                f"{i},{j}",
                f"{i}, {j}",
                f"({i},{j})",
                f"({i}, {j})",
                f"[{i},{j}]",
                f"[{i}, {j}]",
                f"{i}_{j}",
            )
            for key in pair_keys:
                if key in weights:
                    return weights[key]

            if len(weights) == len(nodes):
                row = weights[i] if i in weights else weights[str(i)]
                if isinstance(row, Mapping):
                    return row[j] if j in row else row[str(j)]
                return row[j]

            if len(weights) == len(ordered_pairs):
                position = pair_positions[(i, j)]
            elif len(weights) == len(nodes) ** 2:
                position = i * len(nodes) + j
            else:
                raise ValueError("Unsupported weights mapping format.")

            return (
                weights[position]
                if position in weights
                else weights[str(position)]
            )

        if len(weights) == len(nodes):
            return weights[i][j]
        if len(weights) == len(ordered_pairs):
            return weights[pair_positions[(i, j)]]
        if len(weights) == len(nodes) ** 2:
            return weights[i * len(nodes) + j]

        raise ValueError(
            "weights must contain five rows, 20 ordered-pair values, "
            "or 25 matrix values."
        )

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.ordered_pairs = pyo.Set(
        dimen=2, initialize=ordered_pairs, ordered=True
    )

    model.dispersion_weights = pyo.Param(
        model.ordered_pairs,
        initialize={
            (i, j): read_weight(i, j) for i, j in ordered_pairs
        },
        within=pyo.Reals,
    )
    model.facility_count_target = pyo.Param(
        initialize=num_facilities, within=pyo.Reals
    )

    model.selected = pyo.Var(model.nodes, domain=pyo.Binary)
    model.pair_active = pyo.Var(
        model.ordered_pairs, domain=pyo.Binary
    )

    model.facility_count_constraint = pyo.Constraint(
        expr=sum(model.selected[i] for i in model.nodes)
        == model.facility_count_target
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

    model.first_endpoint_constraint = pyo.Constraint(
        model.ordered_pairs, rule=first_endpoint_rule
    )
    model.second_endpoint_constraint = pyo.Constraint(
        model.ordered_pairs, rule=second_endpoint_rule
    )
    model.both_endpoints_constraint = pyo.Constraint(
        model.ordered_pairs, rule=both_endpoints_rule
    )

    model.total_dispersion = pyo.Objective(
        expr=sum(
            model.dispersion_weights[i, j] * model.pair_active[i, j]
            for i, j in model.ordered_pairs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_dispersion))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}