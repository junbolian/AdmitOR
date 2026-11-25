# IR: {"sets":{"N":[0,1,2,3],"A":"ordered pairs (i,j) in N x N with i != j, lexicographic order"},"params":{"pair_weights":"12 coefficients indexed by A in order","facilities_to_select":"required facility count"},"variables":{"x[i]":"binary for i in N","z[i,j]":"binary for (i,j) in A"},"constraints":["sum(x[i] for i in N) == facilities_to_select","z[i,j] <= x[i] for (i,j) in A","z[i,j] <= x[j] for (i,j) in A","z[i,j] >= x[i] + x[j] - 1 for (i,j) in A"],"objective":"maximize sum(pair_weights[i,j] * z[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using pair_weights supplied as a sequence in ordered-pair order."""
    pair_weights = params["pair_weights"]
    facilities_to_select = params["facilities_to_select"]

    nodes = range(4)
    ordered_pairs = [
        (i, j) for i in nodes for j in nodes if i != j
    ]

    if len(pair_weights) != len(ordered_pairs):
        raise ValueError("pair_weights must contain exactly 12 coefficients.")

    weight_data = {
        pair: pair_weights[position]
        for position, pair in enumerate(ordered_pairs)
    }

    model = pyo.ConcreteModel()

    model.locations = pyo.Set(initialize=nodes, ordered=True)
    model.ordered_pairs = pyo.Set(
        dimen=2, initialize=ordered_pairs, ordered=True
    )

    model.dispersion_weights = pyo.Param(
        model.ordered_pairs,
        initialize=weight_data,
        within=pyo.Reals,
    )
    model.required_facilities = pyo.Param(
        initialize=facilities_to_select,
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.locations, domain=pyo.Binary)
    model.z = pyo.Var(model.ordered_pairs, domain=pyo.Binary)

    model.facility_count = pyo.Constraint(
        expr=sum(model.x[i] for i in model.locations)
        == model.required_facilities
    )

    model.pair_first_selected = pyo.Constraint(
        model.ordered_pairs,
        rule=lambda mdl, i, j: mdl.z[i, j] <= mdl.x[i],
    )
    model.pair_second_selected = pyo.Constraint(
        model.ordered_pairs,
        rule=lambda mdl, i, j: mdl.z[i, j] <= mdl.x[j],
    )
    model.pair_both_selected = pyo.Constraint(
        model.ordered_pairs,
        rule=lambda mdl, i, j: (
            mdl.z[i, j] >= mdl.x[i] + mdl.x[j] - 1
        ),
    )

    model.total_dispersion = pyo.Objective(
        expr=sum(
            model.dispersion_weights[i, j] * model.z[i, j]
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