# IR: {"sets":{"I":"0..6","B":"0..6"},"params":{"item_weights":"weight indexed by I, from params['item_weights']","bin_capacity":"from params['bin_capacity']"},"variables":{"x[i,b]":"binary: item i assigned to bin b","y[b]":"binary: bin b used"},"constraints":["For each i: sum_b x[i,b] = 1","For each b: sum_i item_weights[i]*x[i,b] <= bin_capacity*y[b]","For each i,b: x[i,b] <= y[b]","For each b: y[b] <= sum_i x[i,b]"],"objective":"minimize sum_b y[b]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    item_weights = params["item_weights"]
    bin_capacity = params["bin_capacity"]

    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, 6)
    model.B = pyo.RangeSet(0, 6)

    model.item_weights = pyo.Param(
        model.I, initialize=lambda mdl, i: item_weights[i]
    )
    model.bin_capacity = pyo.Param(initialize=bin_capacity)

    model.x = pyo.Var(model.I, model.B, domain=pyo.Binary)
    model.y = pyo.Var(model.B, domain=pyo.Binary)

    model.item_assignment = pyo.Constraint(
        model.I,
        rule=lambda mdl, i: sum(mdl.x[i, b] for b in mdl.B) == 1,
    )

    model.bin_capacity_limit = pyo.Constraint(
        model.B,
        rule=lambda mdl, b: sum(
            mdl.item_weights[i] * mdl.x[i, b] for i in mdl.I
        ) <= mdl.bin_capacity * mdl.y[b],
    )

    model.assignment_requires_usage = pyo.Constraint(
        model.I,
        model.B,
        rule=lambda mdl, i, b: mdl.x[i, b] <= mdl.y[b],
    )

    model.usage_requires_assignment = pyo.Constraint(
        model.B,
        rule=lambda mdl, b: mdl.y[b] <= sum(mdl.x[i, b] for i in mdl.I),
    )

    model.total_bins = pyo.Objective(
        expr=sum(model.y[b] for b in model.B),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_bins))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}