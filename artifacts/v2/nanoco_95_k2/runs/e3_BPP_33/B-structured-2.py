# IR: {"sets":{"objects":"0..11","blocks":"0..11"},"params":{"memory_sizes":"object sizes from params['memory_sizes']","block_capacity":"block capacity from params['block_capacity']"},"variables":{"assigned[i,b]":"Binary","allocated[b]":"Binary"},"constraints":["For each object i: sum_b assigned[i,b] = 1","For each object i and block b: assigned[i,b] <= allocated[b]","For each block b: sum_i memory_sizes[i]*assigned[i,b] <= block_capacity*allocated[b]"},"objective":"Minimize sum_b allocated[b]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    memory_sizes = params["memory_sizes"]
    block_capacity = params["block_capacity"]

    model = pyo.ConcreteModel()
    model.objects = pyo.RangeSet(0, 11)
    model.blocks = pyo.RangeSet(0, 11)

    model.object_sizes = pyo.Param(
        model.objects,
        initialize={i: memory_sizes[i] for i in model.objects},
        within=pyo.NonNegativeReals,
    )
    model.capacity_limit = pyo.Param(
        initialize=block_capacity,
        within=pyo.NonNegativeReals,
    )

    model.assigned = pyo.Var(
        model.objects, model.blocks, domain=pyo.Binary
    )
    model.allocated = pyo.Var(model.blocks, domain=pyo.Binary)

    def assignment_rule(instance, i):
        return sum(
            instance.assigned[i, b] for b in instance.blocks
        ) == 1

    model.assignment_constraints = pyo.Constraint(
        model.objects, rule=assignment_rule
    )

    def allocation_link_rule(instance, i, b):
        return instance.assigned[i, b] <= instance.allocated[b]

    model.allocation_links = pyo.Constraint(
        model.objects, model.blocks, rule=allocation_link_rule
    )

    def capacity_rule(instance, b):
        return sum(
            instance.object_sizes[i] * instance.assigned[i, b]
            for i in instance.objects
        ) <= instance.capacity_limit * instance.allocated[b]

    model.capacity_constraints = pyo.Constraint(
        model.blocks, rule=capacity_rule
    )

    model.total_blocks = pyo.Objective(
        expr=sum(model.allocated[b] for b in model.blocks),
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