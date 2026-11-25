# IR: {"sets":{"N":"range(num_facilities)","A":"[(i,j) for i in N for j in N if i != j]"},"params":{"num_facilities":"params['num_facilities']","facilities_to_select":"params['facilities_to_select']","dispersion_scores":"params['dispersion_scores'], in A order (or keyed by (i,j))"},"variables":{"x[i]":"binary, i in N","y[i,j]":"binary, (i,j) in A"},"constraints":["sum(x[i] for i in N) == facilities_to_select","y[i,j] <= x[i] for (i,j) in A","y[i,j] <= x[j] for (i,j) in A","y[i,j] >= x[i] + x[j] - 1 for (i,j) in A"],"objective":"maximize sum(dispersion_scores[i,j] * y[i,j] for (i,j) in A)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_facilities = params["num_facilities"]
    facilities_to_select = params["facilities_to_select"]
    dispersion_scores = params["dispersion_scores"]

    nodes = list(range(num_facilities))
    pairs = [(i, j) for i in nodes for j in nodes if i != j]

    if isinstance(dispersion_scores, Mapping):
        scores = {(i, j): dispersion_scores[(i, j)] for i, j in pairs}
    else:
        if len(dispersion_scores) != len(pairs):
            raise ValueError("dispersion_scores must contain one score per ordered pair.")
        scores = dict(zip(pairs, dispersion_scores))

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.pairs = pyo.Set(initialize=pairs, dimen=2, ordered=True)

    model.required_count = pyo.Param(initialize=facilities_to_select)
    model.pair_score = pyo.Param(model.pairs, initialize=scores)

    model.x = pyo.Var(model.nodes, domain=pyo.Binary)
    model.y = pyo.Var(model.pairs, domain=pyo.Binary)

    model.selection_count = pyo.Constraint(
        expr=pyo.quicksum(model.x[i] for i in model.nodes)
        == model.required_count
    )

    model.pair_first_selected = pyo.Constraint(
        model.pairs,
        rule=lambda mdl, i, j: mdl.y[i, j] <= mdl.x[i],
    )
    model.pair_second_selected = pyo.Constraint(
        model.pairs,
        rule=lambda mdl, i, j: mdl.y[i, j] <= mdl.x[j],
    )
    model.pair_activation = pyo.Constraint(
        model.pairs,
        rule=lambda mdl, i, j: mdl.y[i, j] >= mdl.x[i] + mdl.x[j] - 1,
    )

    model.total_dispersion = pyo.Objective(
        expr=pyo.quicksum(
            model.pair_score[i, j] * model.y[i, j]
            for i, j in model.pairs
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