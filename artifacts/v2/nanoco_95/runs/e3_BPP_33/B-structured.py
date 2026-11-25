# IR: {"sets":{"I":"0..len(item_sizes)-1","B":"0..len(item_sizes)-1"},"params":{"item_sizes":"params['item_sizes']","block_capacity":"params['block_capacity']"},"variables":{"assignment[i,b]":"binary; object i assigned to block b","block_used[b]":"binary; block b allocated"},"constraints":["For each i: sum_b assignment[i,b] = 1","For each b: sum_i item_sizes[i]*assignment[i,b] <= block_capacity*block_used[b]","For each i,b: assignment[i,b] <= block_used[b]"],"objective":"minimize sum_b block_used[b]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    item_sizes = list(params["item_sizes"])
    block_capacity = params["block_capacity"]
    object_count = len(item_sizes)

    model = pyo.ConcreteModel()

    model.objects = pyo.Set(initialize=range(object_count), ordered=True)
    model.blocks = pyo.Set(initialize=range(object_count), ordered=True)

    model.object_size = pyo.Param(
        model.objects,
        initialize={idx: size for idx, size in enumerate(item_sizes)},
    )
    model.capacity = pyo.Param(initialize=block_capacity)

    model.assignment = pyo.Var(
        model.objects, model.blocks, domain=pyo.Binary
    )
    model.block_used = pyo.Var(model.blocks, domain=pyo.Binary)

    def assignment_rule(instance, object_idx):
        return (
            sum(
                instance.assignment[object_idx, block_idx]
                for block_idx in instance.blocks
            )
            == 1
        )

    model.exactly_one_block = pyo.Constraint(
        model.objects, rule=assignment_rule
    )

    def capacity_rule(instance, block_idx):
        return (
            sum(
                instance.object_size[object_idx]
                * instance.assignment[object_idx, block_idx]
                for object_idx in instance.objects
            )
            <= instance.capacity * instance.block_used[block_idx]
        )

    model.block_capacity_limit = pyo.Constraint(
        model.blocks, rule=capacity_rule
    )

    def allocation_rule(instance, object_idx, block_idx):
        return (
            instance.assignment[object_idx, block_idx]
            <= instance.block_used[block_idx]
        )

    model.assignment_requires_allocation = pyo.Constraint(
        model.objects, model.blocks, rule=allocation_rule
    )

    model.total_blocks = pyo.Objective(
        expr=sum(model.block_used[block_idx] for block_idx in model.blocks),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_blocks))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}