# IR: {"sets":{"objects":"0..11","blocks":"0..11"},"params":{"memory_sizes":"object sizes read from params","block_capacity":"block capacity read from params"},"variables":{"assignment[i,b]":"binary","block_used[b]":"binary"},"constraints":["For each object i: sum_b assignment[i,b] = 1","For each block b: sum_i memory_sizes[i]*assignment[i,b] <= block_capacity*block_used[b]","For each object i and block b: assignment[i,b] <= block_used[b]"],"objective":"minimize sum_b block_used[b]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    memory_sizes = list(params["memory_sizes"])
    block_capacity = params["block_capacity"]

    if len(memory_sizes) != 12:
        raise ValueError("memory_sizes must contain exactly 12 entries.")
    if any(size < 0 for size in memory_sizes) or block_capacity < 0:
        raise ValueError("Memory sizes and block capacity must be nonnegative.")

    model = pyo.ConcreteModel()
    model.objects = pyo.RangeSet(0, 11)
    model.blocks = pyo.RangeSet(0, 11)

    model.object_size = pyo.Param(
        model.objects,
        initialize={idx: memory_sizes[idx] for idx in range(12)},
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        initialize=block_capacity,
        within=pyo.NonNegativeReals,
    )

    model.assignment = pyo.Var(
        model.objects, model.blocks, domain=pyo.Binary
    )
    model.block_used = pyo.Var(model.blocks, domain=pyo.Binary)

    def assignment_rule(instance, object_idx):
        return sum(
            instance.assignment[object_idx, block_idx]
            for block_idx in instance.blocks
        ) == 1

    model.assign_once = pyo.Constraint(
        model.objects, rule=assignment_rule
    )

    def capacity_rule(instance, block_idx):
        return sum(
            instance.object_size[object_idx]
            * instance.assignment[object_idx, block_idx]
            for object_idx in instance.objects
        ) <= instance.capacity * instance.block_used[block_idx]

    model.block_capacity_limit = pyo.Constraint(
        model.blocks, rule=capacity_rule
    )

    def activation_rule(instance, object_idx, block_idx):
        return (
            instance.assignment[object_idx, block_idx]
            <= instance.block_used[block_idx]
        )

    model.assignment_activation = pyo.Constraint(
        model.objects, model.blocks, rule=activation_rule
    )

    model.total_blocks = pyo.Objective(
        expr=sum(
            model.block_used[block_idx] for block_idx in model.blocks
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Leave the variables unset and determine success below.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_blocks))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}