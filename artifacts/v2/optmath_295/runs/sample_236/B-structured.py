# IR: {"sets":{"I":"0..6","B":"0..6"},"params":{"bin_capacity":"params['bin_capacity']","item_weights[i]":"params['item_weights'][i]"},"variables":{"assigned[i,b]":"Binary","bin_used[b]":"Binary"},"constraints":["sum(b in B, assigned[i,b]) == 1 for each i in I","sum(i in I, item_weights[i]*assigned[i,b]) <= bin_capacity*bin_used[b] for each b in B","assigned[i,b] <= bin_used[b] for each i in I, b in B"],"objective":"minimize sum(b in B, bin_used[b])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.item_ids = pyo.RangeSet(0, 6)
    model.bin_ids = pyo.RangeSet(0, 6)

    model.bin_capacity = pyo.Param(
        initialize=params["bin_capacity"],
        within=pyo.NonNegativeReals,
    )
    model.item_weights = pyo.Param(
        model.item_ids,
        initialize={
            item_id: params["item_weights"][item_id]
            for item_id in model.item_ids
        },
        within=pyo.NonNegativeReals,
    )

    model.assigned = pyo.Var(
        model.item_ids, model.bin_ids, domain=pyo.Binary
    )
    model.bin_used = pyo.Var(model.bin_ids, domain=pyo.Binary)

    def assignment_rule(model, item_id):
        return sum(
            model.assigned[item_id, bin_id]
            for bin_id in model.bin_ids
        ) == 1

    model.item_assignment = pyo.Constraint(
        model.item_ids, rule=assignment_rule
    )

    def capacity_rule(model, bin_id):
        return sum(
            model.item_weights[item_id] * model.assigned[item_id, bin_id]
            for item_id in model.item_ids
        ) <= model.bin_capacity * model.bin_used[bin_id]

    model.capacity_limit = pyo.Constraint(
        model.bin_ids, rule=capacity_rule
    )

    def usage_rule(model, item_id, bin_id):
        return model.assigned[item_id, bin_id] <= model.bin_used[bin_id]

    model.usage_link = pyo.Constraint(
        model.item_ids, model.bin_ids, rule=usage_rule
    )

    model.total_bins = pyo.Objective(
        expr=sum(model.bin_used[bin_id] for bin_id in model.bin_ids),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_bins))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}