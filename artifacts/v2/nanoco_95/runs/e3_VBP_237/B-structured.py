# IR: {"sets":{"procedures":"0..9","slots":"0..9","resources":"0..1"},"params":{"capacities":"nonnegative capacity[resource], from params['capacities']","weights":"nonnegative consumption[procedure,resource], from params['weights']"},"variables":{"assigned[procedure,slot]":"binary","used[slot]":"binary"},"constraints":["For each procedure: sum_slot assigned[procedure,slot] = 1.","For each procedure and slot: assigned[procedure,slot] <= used[slot].","For each slot and resource: sum_procedure weights[procedure,resource]*assigned[procedure,slot] <= capacities[resource]*used[slot]."],"objective":"Minimize sum_slot used[slot]."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = params["capacities"]
    weights = params["weights"]

    model = pyo.ConcreteModel()

    model.procedures = pyo.RangeSet(0, 9)
    model.slots = pyo.RangeSet(0, 9)
    model.resources = pyo.RangeSet(0, 1)

    model.capacities = pyo.Param(
        model.resources,
        initialize=lambda mdl, resource: capacities[resource],
        within=pyo.NonNegativeReals,
    )
    model.weights = pyo.Param(
        model.procedures,
        model.resources,
        initialize=lambda mdl, procedure, resource: weights[procedure][resource],
        within=pyo.NonNegativeReals,
    )

    # Ten candidate slots suffice: any feasible packing of ten procedures
    # uses at most ten nonempty slots.
    model.assigned = pyo.Var(
        model.procedures,
        model.slots,
        domain=pyo.Binary,
    )
    model.used = pyo.Var(model.slots, domain=pyo.Binary)

    def assignment_rule(mdl, procedure):
        return sum(
            mdl.assigned[procedure, slot] for slot in mdl.slots
        ) == 1

    model.assignment_constraints = pyo.Constraint(
        model.procedures,
        rule=assignment_rule,
    )

    def activation_rule(mdl, procedure, slot):
        return mdl.assigned[procedure, slot] <= mdl.used[slot]

    model.activation_constraints = pyo.Constraint(
        model.procedures,
        model.slots,
        rule=activation_rule,
    )

    def capacity_rule(mdl, slot, resource):
        return sum(
            mdl.weights[procedure, resource] * mdl.assigned[procedure, slot]
            for procedure in mdl.procedures
        ) <= mdl.capacities[resource] * mdl.used[slot]

    model.capacity_constraints = pyo.Constraint(
        model.slots,
        model.resources,
        rule=capacity_rule,
    )

    model.total_slots = pyo.Objective(
        expr=sum(model.used[slot] for slot in model.slots),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_slots))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}