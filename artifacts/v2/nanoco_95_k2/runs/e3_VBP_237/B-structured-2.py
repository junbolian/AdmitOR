# IR: {"sets":{"I":"0..9 procedures","S":"0..9 candidate slots","D":"0..1 resource dimensions"},"params":{"capacities":"params['capacities'][d], nonnegative real","weights":"params['weights'][i][d], nonnegative real"},"variables":{"x[i,s]":"binary; procedure i assigned to slot s","y[s]":"binary; slot s activated"},"constraints":["For each i: sum_s x[i,s] = 1","For each s,d: sum_i weights[i,d]*x[i,s] <= capacities[d]*y[s]","For each i,s: x[i,s] <= y[s]"],"objective":"minimize sum_s y[s]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.procedures = pyo.RangeSet(0, 9)
    model.slots = pyo.RangeSet(0, 9)
    model.dimensions = pyo.RangeSet(0, 1)

    model.capacities = pyo.Param(
        model.dimensions,
        initialize={
            dim: params["capacities"][dim]
            for dim in model.dimensions
        },
        within=pyo.NonNegativeReals,
    )
    model.weights = pyo.Param(
        model.procedures,
        model.dimensions,
        initialize={
            (procedure, dim): params["weights"][procedure][dim]
            for procedure in model.procedures
            for dim in model.dimensions
        },
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(
        model.procedures, model.slots, domain=pyo.Binary
    )
    model.y = pyo.Var(model.slots, domain=pyo.Binary)

    def assignment_rule(current_model, procedure):
        return sum(
            current_model.x[procedure, slot]
            for slot in current_model.slots
        ) == 1

    model.assignment_constraints = pyo.Constraint(
        model.procedures, rule=assignment_rule
    )

    def capacity_rule(current_model, slot, dim):
        return sum(
            current_model.weights[procedure, dim]
            * current_model.x[procedure, slot]
            for procedure in current_model.procedures
        ) <= current_model.capacities[dim] * current_model.y[slot]

    model.capacity_constraints = pyo.Constraint(
        model.slots, model.dimensions, rule=capacity_rule
    )

    def activation_rule(current_model, procedure, slot):
        return (
            current_model.x[procedure, slot]
            <= current_model.y[slot]
        )

    model.activation_constraints = pyo.Constraint(
        model.procedures, model.slots, rule=activation_rule
    )

    model.total_slots = pyo.Objective(
        expr=sum(model.y[slot] for slot in model.slots),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_slots))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}