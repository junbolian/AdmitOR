# IR: {"sets":{"I":"range(params['num_items'])","B":"range(params['num_bins'])"},"params":{"bin_capacity":"params['bin_capacity']","item_weights":"params['item_weights']","num_bins":"params['num_bins']","num_items":"params['num_items']"},"variables":{"used[b]":"binary, b in B","assigned[i,b]":"binary, (i,b) in I x B"},"constraints":["sum(assigned[i,b] for b in B) = 1 for each i in I","sum(item_weights[i]*assigned[i,b] for i in I) <= bin_capacity*used[b] for each b in B","assigned[i,b] <= used[b] for each (i,b) in I x B"],"objective":"minimize sum(used[b] for b in B)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_bins = params["num_bins"]
    num_items = params["num_items"]
    bin_capacity = params["bin_capacity"]
    item_weights = params["item_weights"]

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=range(num_items), ordered=True)
    model.B = pyo.Set(initialize=range(num_bins), ordered=True)

    model.capacity = pyo.Param(
        initialize=bin_capacity,
        within=pyo.NonNegativeReals,
    )
    model.weight = pyo.Param(
        model.I,
        initialize={item_idx: item_weights[item_idx]
                    for item_idx in range(num_items)},
        within=pyo.NonNegativeReals,
    )

    model.used = pyo.Var(model.B, domain=pyo.Binary)
    model.assigned = pyo.Var(model.I, model.B, domain=pyo.Binary)

    def assignment_rule(current_model, item_idx):
        # Tuple form also handles an empty bin set without a Boolean constraint.
        return (
            1,
            sum(current_model.assigned[item_idx, bin_idx]
                for bin_idx in current_model.B),
            1,
        )

    model.item_assignment = pyo.Constraint(
        model.I,
        rule=assignment_rule,
    )

    def capacity_rule(current_model, bin_idx):
        return (
            sum(
                current_model.weight[item_idx]
                * current_model.assigned[item_idx, bin_idx]
                for item_idx in current_model.I
            )
            <= current_model.capacity * current_model.used[bin_idx]
        )

    model.bin_capacity_limit = pyo.Constraint(
        model.B,
        rule=capacity_rule,
    )

    def usage_link_rule(current_model, item_idx, bin_idx):
        return (
            current_model.assigned[item_idx, bin_idx]
            <= current_model.used[bin_idx]
        )

    model.assignment_usage_link = pyo.Constraint(
        model.I,
        model.B,
        rule=usage_link_rule,
    )

    model.total_bins = pyo.Objective(
        expr=sum(model.used[bin_idx] for bin_idx in model.B),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_bins))
    except (ValueError, TypeError, RuntimeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}