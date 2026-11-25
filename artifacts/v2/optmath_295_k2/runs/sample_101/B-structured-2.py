# IR: {"sets":{"N":"range(params['num_nodes'])","P":"{(i,j) in N x N: i != j}"},"params":{"coverage_scores":"d[i,j] for ordered pairs in P; accepts a matrix, nested mapping, tuple-keyed mapping, or row-major flat sequence with or without diagonal entries","num_centers":"required center count","num_nodes":"number of nodes"},"variables":{"x[i]":"binary for i in N","z[i,j]":"binary for (i,j) in P"},"constraints":["sum(x[i] for i in N) = num_centers","z[i,j] <= x[i] for (i,j) in P","z[i,j] <= x[j] for (i,j) in P","z[i,j] >= x[i] + x[j] - 1 for (i,j) in P"],"objective":"maximize sum(d[i,j] * z[i,j] for (i,j) in P)"}

from collections.abc import Mapping
from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coverage_scores = params["coverage_scores"]
    num_centers = params["num_centers"]
    num_nodes = params["num_nodes"]

    flat_scores = (
        not isinstance(coverage_scores, Mapping)
        and len(coverage_scores) > 0
        and isinstance(coverage_scores[0], Number)
    )

    flat_has_diagonal = False
    if flat_scores:
        score_count = len(coverage_scores)
        if score_count == num_nodes * num_nodes:
            flat_has_diagonal = True
        elif score_count != num_nodes * (num_nodes - 1):
            return {"objective": None, "status": "invalid_score_count"}

    def read_score(i, j):
        if flat_scores:
            if flat_has_diagonal:
                return coverage_scores[i * num_nodes + j]

            # Row-major ordered pairs, skipping each row's diagonal.
            offset = i * (num_nodes - 1) + j - (1 if j > i else 0)
            return coverage_scores[offset]

        if isinstance(coverage_scores, Mapping):
            if (i, j) in coverage_scores:
                return coverage_scores[(i, j)]
            row_key = i if i in coverage_scores else str(i)
            row = coverage_scores[row_key]
        else:
            row = coverage_scores[i]

        if isinstance(row, Mapping):
            column_key = j if j in row else str(j)
            return row[column_key]
        return row[j]

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(
        initialize=range(num_nodes),
        ordered=True,
    )
    model.pairs = pyo.Set(
        dimen=2,
        initialize=(
            (i, j)
            for i in range(num_nodes)
            for j in range(num_nodes)
            if i != j
        ),
        ordered=True,
    )

    model.center_count = pyo.Param(
        initialize=num_centers,
        within=pyo.Reals,
        mutable=True,
    )
    model.coverage = pyo.Param(
        model.pairs,
        initialize=lambda mdl, i, j: read_score(i, j),
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.nodes, domain=pyo.Binary)
    model.z = pyo.Var(model.pairs, domain=pyo.Binary)

    model.exact_centers = pyo.Constraint(
        expr=pyo.quicksum(model.x[i] for i in model.nodes)
        == model.center_count
    )
    model.pair_first = pyo.Constraint(
        model.pairs,
        rule=lambda mdl, i, j: mdl.z[i, j] <= mdl.x[i],
    )
    model.pair_second = pyo.Constraint(
        model.pairs,
        rule=lambda mdl, i, j: mdl.z[i, j] <= mdl.x[j],
    )
    model.pair_both = pyo.Constraint(
        model.pairs,
        rule=lambda mdl, i, j: mdl.z[i, j] >= mdl.x[i] + mdl.x[j] - 1,
    )

    model.total_coverage = pyo.Objective(
        expr=pyo.quicksum(
            model.coverage[i, j] * model.z[i, j]
            for i, j in model.pairs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_coverage))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}