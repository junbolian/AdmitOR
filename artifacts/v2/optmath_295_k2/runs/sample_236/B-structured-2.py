# IR: {"sets":{"item_ids":[0,1,2,3,4,5,6],"bin_ids":[0,1,2,3,4,5,6]},"params":{"bin_capacity":"params['bin_capacity']","item_weight[i]":"params['item_weight_' + str(i)]"},"variables":{"assigned[i,b]":"Binary","bin_used[b]":"Binary"},"constraints":["sum(assigned[i,b] for b in bin_ids) == 1 for each i in item_ids","sum(item_weight[i]*assigned[i,b] for i in item_ids) <= bin_capacity*bin_used[b] for each b in bin_ids","assigned[i,b] <= bin_used[b] for each i in item_ids and b in bin_ids"],"objective":"minimize sum(bin_used[b] for b in bin_ids)"}

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
    model.item_weight = pyo.Param(
        model.item_ids,
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

    model.assigned = pyo.Var(
        model.item_ids,
        model.bin_ids,
        domain=pyo.Binary,
    )
    model.bin_used = pyo.Var(model.bin_ids, domain=pyo.Binary)

    def assignment_rule(block, item_id):
        return sum(
            block.assigned[item_id, bin_id]
            for bin_id in block.bin_ids
        ) == 1

    model.item_assignment = pyo.Constraint(
        model.item_ids,
        rule=assignment_rule,
    )

    def capacity_rule(block, bin_id):
        return sum(
            block.item_weight[item_id] * block.assigned[item_id, bin_id]
            for item_id in block.item_ids
        ) <= block.bin_capacity * block.bin_used[bin_id]

    model.capacity_limit = pyo.Constraint(
        model.bin_ids,
        rule=capacity_rule,
    )

    def usage_rule(block, item_id, bin_id):
        return block.assigned[item_id, bin_id] <= block.bin_used[bin_id]

    model.usage_link = pyo.Constraint(
        model.item_ids,
        model.bin_ids,
        rule=usage_rule,
    )

    model.total_bins = pyo.Objective(
        expr=sum(
            model.bin_used[bin_id]
            for bin_id in model.bin_ids
        ),
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