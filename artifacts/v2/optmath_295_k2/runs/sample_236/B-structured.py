# IR: {"sets":{"I":"0..6","B":"0..6"},"params":{"bin_capacity":"nonnegative real","item_weight_0":"nonnegative real","item_weight_1":"nonnegative real","item_weight_2":"nonnegative real","item_weight_3":"nonnegative real","item_weight_4":"nonnegative real","item_weight_5":"nonnegative real","item_weight_6":"nonnegative real"},"decision_variables":{"x[i,b]":"binary; item i assigned to bin b","y[b]":"binary; bin b used"},"constraints":["sum(b in B, x[i,b]) = 1 for each i in I","sum(i in I, item_weight_i*x[i,b]) <= bin_capacity*y[b] for each b in B","x[i,b] <= y[b] for each i in I, b in B"],"objective":"minimize sum(b in B, y[b])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 6)
    model.B = pyo.RangeSet(0, 6)

    model.bin_capacity = pyo.Param(
        initialize=params["bin_capacity"],
        within=pyo.NonNegativeReals,
    )
    model.item_weight = pyo.Param(
        model.I,
        initialize={
            0: params["item_weight_0"],
            1: params["item_weight_1"],
            2: params["item_weight_2"],
            3: params["item_weight_3"],
            4: params["item_weight_4"],
            5: params["item_weight_5"],
            6: params["item_weight_6"],
        },
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.I, model.B, domain=pyo.Binary)
    model.y = pyo.Var(model.B, domain=pyo.Binary)

    def assignment_rule(instance, item):
        return sum(instance.x[item, bin_id] for bin_id in instance.B) == 1

    model.item_assignment = pyo.Constraint(model.I, rule=assignment_rule)

    def capacity_rule(instance, bin_id):
        return (
            sum(
                instance.item_weight[item] * instance.x[item, bin_id]
                for item in instance.I
            )
            <= instance.bin_capacity * instance.y[bin_id]
        )

    model.bin_capacity_limit = pyo.Constraint(model.B, rule=capacity_rule)

    def usage_rule(instance, item, bin_id):
        return instance.x[item, bin_id] <= instance.y[bin_id]

    model.assignment_requires_usage = pyo.Constraint(
        model.I, model.B, rule=usage_rule
    )

    model.total_bins = pyo.Objective(
        expr=sum(model.y[bin_id] for bin_id in model.B),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when no feasible solution can be loaded.
        # Preserve unexpected runtime errors for the calling harness.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_bins))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}