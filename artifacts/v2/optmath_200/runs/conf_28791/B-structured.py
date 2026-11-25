# IR: {"sets":{"item_ids":"0..7","bin_ids":"0..7"},"params":{"bin_capacity":"params['bin_capacity']","item_weights[i]":"params['item_weights'][i]"},"variables":{"assigned[i,b]":"binary","used[b]":"binary"},"constraints":["sum_b assigned[i,b] = 1 for each i","sum_i item_weights[i]*assigned[i,b] <= bin_capacity*used[b] for each b","assigned[i,b] <= used[b] for each i,b"],"objective":"minimize sum_b used[b]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.item_ids = pyo.RangeSet(0, 7)
    model.bin_ids = pyo.RangeSet(0, 7)

    model.bin_capacity = pyo.Param(initialize=params["bin_capacity"])
    model.item_weights = pyo.Param(
        model.item_ids,
        initialize={
            item_id: params["item_weights"][item_id]
            for item_id in model.item_ids
        },
    )

    model.assigned = pyo.Var(
        model.item_ids, model.bin_ids, domain=pyo.Binary
    )
    model.used = pyo.Var(model.bin_ids, domain=pyo.Binary)

    def assignment_rule(mod, item_id):
        return sum(
            mod.assigned[item_id, bin_id] for bin_id in mod.bin_ids
        ) == 1

    model.assignment_constraints = pyo.Constraint(
        model.item_ids, rule=assignment_rule
    )

    def capacity_rule(mod, bin_id):
        return sum(
            mod.item_weights[item_id] * mod.assigned[item_id, bin_id]
            for item_id in mod.item_ids
        ) <= mod.bin_capacity * mod.used[bin_id]

    model.capacity_constraints = pyo.Constraint(
        model.bin_ids, rule=capacity_rule
    )

    def usage_rule(mod, item_id, bin_id):
        return mod.assigned[item_id, bin_id] <= mod.used[bin_id]

    model.usage_constraints = pyo.Constraint(
        model.item_ids, model.bin_ids, rule=usage_rule
    )

    model.total_bins = pyo.Objective(
        expr=sum(model.used[bin_id] for bin_id in model.bin_ids),
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