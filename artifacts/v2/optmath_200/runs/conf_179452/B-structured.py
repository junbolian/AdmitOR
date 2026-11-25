# IR: {"sets":{"N":[0,1,2,3,4],"A":"{(i,j) in N x N: i != j}"},"params":{"dispersion_weights":"real weight for each ordered pair in A, read from params","num_facilities_selected":"cardinality RHS, read from params"},"variables":{"selected[i]":"binary, i in N","paired[i,j]":"binary, (i,j) in A"},"constraints":["sum(selected[i] for i in N) == num_facilities_selected","paired[i,j] <= selected[i] for (i,j) in A","paired[i,j] <= selected[j] for (i,j) in A","paired[i,j] >= selected[i] + selected[j] - 1 for (i,j) in A"],"objective":"maximize sum(dispersion_weights[i,j] * paired[i,j] for (i,j) in A)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    dispersion_weights accepts a nested matrix/dictionary or a dictionary
    keyed by (i, j). Nested dictionaries may use integer or string indices.
    """
    dispersion_weights = params["dispersion_weights"]
    num_facilities_selected = params["num_facilities_selected"]

    def read_weight(i, j):
        if isinstance(dispersion_weights, Mapping):
            if (i, j) in dispersion_weights:
                return dispersion_weights[(i, j)]
            row = dispersion_weights[
                i if i in dispersion_weights else str(i)
            ]
        else:
            row = dispersion_weights[i]

        if isinstance(row, Mapping):
            return row[j if j in row else str(j)]
        return row[j]

    model = pyo.ConcreteModel()
    model.locations = pyo.Set(initialize=range(5), ordered=True)
    model.ordered_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(5)
            for j in range(5)
            if i != j
        ],
        ordered=True,
    )

    model.pair_weights = pyo.Param(
        model.ordered_pairs,
        initialize={
            (i, j): read_weight(i, j)
            for i, j in model.ordered_pairs
        },
        within=pyo.Reals,
    )
    model.required_facilities = pyo.Param(
        initialize=num_facilities_selected,
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.locations, domain=pyo.Binary)
    model.paired = pyo.Var(model.ordered_pairs, domain=pyo.Binary)

    model.facility_count = pyo.Constraint(
        expr=sum(model.selected[i] for i in model.locations)
        == model.required_facilities
    )
    model.pair_first_bound = pyo.Constraint(
        model.ordered_pairs,
        rule=lambda mdl, i, j: mdl.paired[i, j] <= mdl.selected[i],
    )
    model.pair_second_bound = pyo.Constraint(
        model.ordered_pairs,
        rule=lambda mdl, i, j: mdl.paired[i, j] <= mdl.selected[j],
    )
    model.pair_lower_bound = pyo.Constraint(
        model.ordered_pairs,
        rule=lambda mdl, i, j: (
            mdl.paired[i, j] >= mdl.selected[i] + mdl.selected[j] - 1
        ),
    )

    model.total_dispersion = pyo.Objective(
        expr=sum(
            model.pair_weights[i, j] * model.paired[i, j]
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