# IR: {"sets":{"N":"range(num_nodes)","A":"{(i,j) in N x N: i != j}"},"params":{"num_nodes":"params['num_nodes']","num_centers":"params['num_centers']","coverage_scores":"params['coverage_scores']; tuple-keyed mapping, nested matrix/mapping, or flat row-major sequence with num_nodes^2 entries (including diagonals) or num_nodes*(num_nodes-1) entries (excluding diagonals)"},"variables":{"x[i]":"binary for i in N","z[i,j]":"binary for (i,j) in A"},"constraints":["sum(x[i] for i in N) == num_centers","z[i,j] <= x[i] for (i,j) in A","z[i,j] <= x[j] for (i,j) in A","z[i,j] >= x[i] + x[j] - 1 for (i,j) in A"],"objective":"maximize sum(coverage_scores[i,j] * z[i,j] for (i,j) in A)"}

from collections.abc import Mapping
from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coverage_scores = params["coverage_scores"]
    num_centers = params["num_centers"]
    num_nodes = params["num_nodes"]

    model = pyo.ConcreteModel()

    model.node_count = pyo.Param(
        initialize=num_nodes,
        within=pyo.NonNegativeIntegers,
    )
    model.required_centers = pyo.Param(
        initialize=num_centers,
        within=pyo.NonNegativeIntegers,
    )

    node_count = int(pyo.value(model.node_count))

    def mapping_item(mapping, key):
        return mapping[key] if key in mapping else mapping[str(key)]

    def read_score(i, j):
        if isinstance(coverage_scores, Mapping):
            if (i, j) in coverage_scores:
                return coverage_scores[(i, j)]
            row = mapping_item(coverage_scores, i)
        else:
            row = coverage_scores[i]

        if isinstance(row, Mapping):
            return mapping_item(row, j)

        if not isinstance(row, Number):
            return row[j]

        # Scalar entries indicate a flattened row-major representation.
        entry_count = len(coverage_scores)
        if entry_count == node_count * node_count:
            position = i * node_count + j
        elif entry_count == node_count * (node_count - 1):
            position = i * (node_count - 1) + j - (j > i)
        else:
            raise ValueError(
                "Flat coverage_scores must contain num_nodes**2 or "
                "num_nodes*(num_nodes-1) entries."
            )

        if isinstance(coverage_scores, Mapping):
            return mapping_item(coverage_scores, position)
        return coverage_scores[position]

    model.nodes = pyo.Set(
        initialize=range(node_count),
        ordered=True,
    )
    model.ordered_pairs = pyo.Set(
        dimen=2,
        initialize=(
            (i, j)
            for i in model.nodes
            for j in model.nodes
            if i != j
        ),
        ordered=True,
    )
    model.pair_scores = pyo.Param(
        model.ordered_pairs,
        initialize=lambda mdl, i, j: read_score(i, j),
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.nodes, domain=pyo.Binary)
    model.z = pyo.Var(model.ordered_pairs, domain=pyo.Binary)

    model.center_count_constraint = pyo.Constraint(
        expr=(
            pyo.quicksum(model.x[i] for i in model.nodes)
            == model.required_centers
        )
    )
    model.first_endpoint_constraint = pyo.Constraint(
        model.ordered_pairs,
        rule=lambda mdl, i, j: mdl.z[i, j] <= mdl.x[i],
    )
    model.second_endpoint_constraint = pyo.Constraint(
        model.ordered_pairs,
        rule=lambda mdl, i, j: mdl.z[i, j] <= mdl.x[j],
    )
    model.both_endpoints_constraint = pyo.Constraint(
        model.ordered_pairs,
        rule=lambda mdl, i, j: (
            mdl.z[i, j] >= mdl.x[i] + mdl.x[j] - 1
        ),
    )

    model.total_coverage = pyo.Objective(
        expr=pyo.quicksum(
            model.pair_scores[i, j] * model.z[i, j]
            for i, j in model.ordered_pairs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Continue to objective retrieval only for a missing feasible solution.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_coverage))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}