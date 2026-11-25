# IR: {"sets":{"item_ids":"0..6","container_ids":"0..6"},"params":{"item_weights":"params['item_weights'][i]","container_capacity":"params['container_capacity']"},"variables":{"assigned[i,c]":"Binary","used[c]":"Binary"},"constraints":["For each item i: sum_c assigned[i,c] == 1","For each container c: sum_i item_weights[i]*assigned[i,c] <= container_capacity*used[c]","For each item i and container c: assigned[i,c] <= used[c]","For each container c: used[c] <= sum_i assigned[i,c]"],"objective":"Minimize sum_c used[c]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.item_ids = pyo.RangeSet(0, 6)
    model.container_ids = pyo.RangeSet(0, 6)

    model.item_weights = pyo.Param(
        model.item_ids,
        initialize={
            item: params["item_weights"][item]
            for item in model.item_ids
        },
        within=pyo.Reals,
    )
    model.container_capacity = pyo.Param(
        initialize=params["container_capacity"],
        within=pyo.Reals,
    )

    model.assigned = pyo.Var(
        model.item_ids,
        model.container_ids,
        domain=pyo.Binary,
    )
    model.used = pyo.Var(model.container_ids, domain=pyo.Binary)

    def assignment_rule(model, item):
        return sum(
            model.assigned[item, container]
            for container in model.container_ids
        ) == 1

    model.item_assignment = pyo.Constraint(
        model.item_ids,
        rule=assignment_rule,
    )

    def capacity_rule(model, container):
        return sum(
            model.item_weights[item] * model.assigned[item, container]
            for item in model.item_ids
        ) <= model.container_capacity * model.used[container]

    model.capacity_limit = pyo.Constraint(
        model.container_ids,
        rule=capacity_rule,
    )

    def activation_rule(model, item, container):
        return model.assigned[item, container] <= model.used[container]

    model.assignment_activation = pyo.Constraint(
        model.item_ids,
        model.container_ids,
        rule=activation_rule,
    )

    def occupancy_rule(model, container):
        return model.used[container] <= sum(
            model.assigned[item, container]
            for item in model.item_ids
        )

    model.used_requires_item = pyo.Constraint(
        model.container_ids,
        rule=occupancy_rule,
    )

    model.total_containers = pyo.Objective(
        expr=sum(
            model.used[container]
            for container in model.container_ids
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" not in str(exc).lower():
            raise
        return {"objective": None, "status": "no_feasible_solution"}

    try:
        obj_val = float(pyo.value(model.total_containers))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}