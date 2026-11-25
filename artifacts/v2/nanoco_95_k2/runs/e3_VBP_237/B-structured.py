# IR: {"sets":{"procedures":"0..9","slots":"0..9","dimensions":"0..1"},"params":{"capacities":"nonnegative array[2] from params","weights":"nonnegative array[10][2] from params"},"variables":{"assigned[i,s]":"binary","used[s]":"binary"},"constraints":["sum_s assigned[i,s] = 1 for each procedure i","assigned[i,s] <= used[s] for each procedure i and slot s","sum_i weights[i,d]*assigned[i,s] <= capacities[d]*used[s] for each slot s and dimension d"],"objective":"minimize sum_s used[s]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = params["capacities"]
    weights = params["weights"]

    model = pyo.ConcreteModel()
    model.procedures = pyo.RangeSet(0, 9)
    model.slots = pyo.RangeSet(0, 9)
    model.dimensions = pyo.RangeSet(0, 1)

    model.capacity = pyo.Param(
        model.dimensions,
        initialize=lambda mdl, dim: capacities[dim],
        within=pyo.NonNegativeReals,
    )
    model.requirement = pyo.Param(
        model.procedures,
        model.dimensions,
        initialize=lambda mdl, item, dim: weights[item][dim],
        within=pyo.NonNegativeReals,
    )

    model.assigned = pyo.Var(
        model.procedures, model.slots, domain=pyo.Binary
    )
    model.used = pyo.Var(model.slots, domain=pyo.Binary)

    model.assign_once = pyo.Constraint(
        model.procedures,
        rule=lambda mdl, item: sum(
            mdl.assigned[item, slot] for slot in mdl.slots
        ) == 1,
    )

    model.activation_link = pyo.Constraint(
        model.procedures,
        model.slots,
        rule=lambda mdl, item, slot:
            mdl.assigned[item, slot] <= mdl.used[slot],
    )

    model.resource_limit = pyo.Constraint(
        model.slots,
        model.dimensions,
        rule=lambda mdl, slot, dim: sum(
            mdl.requirement[item, dim] * mdl.assigned[item, slot]
            for item in mdl.procedures
        ) <= mdl.capacity[dim] * mdl.used[slot],
    )

    model.total_slots = pyo.Objective(
        expr=sum(model.used[slot] for slot in model.slots),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Other runtime errors are unexpected and must propagate.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_slots))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}