# IR: {"sets":{"supplies":"0..6","hospitals":"0..6"},"params":{"supply_weights":"nonnegative weight indexed by supplies, read from params","hospital_capacity":"nonnegative capacity, read from params"},"variables":{"assigned[i,h]":"binary","used[h]":"binary"},"constraints":["For each supply i: sum_h assigned[i,h] = 1","For each hospital h: sum_i supply_weights[i]*assigned[i,h] <= hospital_capacity*used[h]","For each supply i and hospital h: assigned[i,h] <= used[h]","For each hospital h: used[h] <= sum_i assigned[i,h]"],"objective":"Minimize sum_h used[h]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.supplies = pyo.RangeSet(0, 6)
    model.hospitals = pyo.RangeSet(0, 6)

    model.supply_weight = pyo.Param(
        model.supplies,
        initialize={
            i: params["supply_weights"][i]
            for i in model.supplies
        },
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        initialize=params["hospital_capacity"],
        within=pyo.NonNegativeReals,
    )

    model.assigned = pyo.Var(
        model.supplies,
        model.hospitals,
        domain=pyo.Binary,
    )
    model.used = pyo.Var(model.hospitals, domain=pyo.Binary)

    def assignment_rule(mdl, i):
        return sum(
            mdl.assigned[i, h] for h in mdl.hospitals
        ) == 1

    model.assignment_constraints = pyo.Constraint(
        model.supplies,
        rule=assignment_rule,
    )

    def capacity_rule(mdl, h):
        return sum(
            mdl.supply_weight[i] * mdl.assigned[i, h]
            for i in mdl.supplies
        ) <= mdl.capacity * mdl.used[h]

    model.capacity_constraints = pyo.Constraint(
        model.hospitals,
        rule=capacity_rule,
    )

    def usage_link_rule(mdl, i, h):
        return mdl.assigned[i, h] <= mdl.used[h]

    model.usage_link_constraints = pyo.Constraint(
        model.supplies,
        model.hospitals,
        rule=usage_link_rule,
    )

    def nonempty_hospital_rule(mdl, h):
        return mdl.used[h] <= sum(
            mdl.assigned[i, h] for i in mdl.supplies
        )

    model.nonempty_hospital_constraints = pyo.Constraint(
        model.hospitals,
        rule=nonempty_hospital_rule,
    )

    model.total_hospitals = pyo.Objective(
        expr=sum(model.used[h] for h in model.hospitals),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_hospitals))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}