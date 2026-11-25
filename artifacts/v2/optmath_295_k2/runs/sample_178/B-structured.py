# IR: {"sets":{"supplies":"0..6","hospitals":"0..6"},"params":{"supply_weights":"params['supply_weights'][i]","hospital_capacity":"params['hospital_capacity']"},"variables":{"assigned[i,h]":"binary","used[h]":"binary"},"constraints":["For each supply i: sum_h assigned[i,h] = 1","For each hospital h: sum_i supply_weights[i]*assigned[i,h] <= hospital_capacity*used[h]","For each supply i and hospital h: assigned[i,h] <= used[h]","For each hospital h: used[h] <= sum_i assigned[i,h]"],"objective":"minimize sum_h used[h]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.supplies = pyo.RangeSet(0, 6)
    model.hospitals = pyo.RangeSet(0, 6)

    model.supply_weights = pyo.Param(
        model.supplies,
        initialize=lambda mdl, supply: params["supply_weights"][supply],
    )
    model.hospital_capacity = pyo.Param(
        initialize=params["hospital_capacity"],
    )

    model.assigned = pyo.Var(
        model.supplies, model.hospitals, domain=pyo.Binary
    )
    model.used = pyo.Var(model.hospitals, domain=pyo.Binary)

    def assignment_rule(mdl, supply):
        return sum(
            mdl.assigned[supply, hospital] for hospital in mdl.hospitals
        ) == 1

    model.assignment_constraints = pyo.Constraint(
        model.supplies, rule=assignment_rule
    )

    def capacity_rule(mdl, hospital):
        return sum(
            mdl.supply_weights[supply] * mdl.assigned[supply, hospital]
            for supply in mdl.supplies
        ) <= mdl.hospital_capacity * mdl.used[hospital]

    model.capacity_constraints = pyo.Constraint(
        model.hospitals, rule=capacity_rule
    )

    def usage_link_rule(mdl, supply, hospital):
        return mdl.assigned[supply, hospital] <= mdl.used[hospital]

    model.usage_link_constraints = pyo.Constraint(
        model.supplies, model.hospitals, rule=usage_link_rule
    )

    def nonempty_rule(mdl, hospital):
        return mdl.used[hospital] <= sum(
            mdl.assigned[supply, hospital] for supply in mdl.supplies
        )

    model.nonempty_constraints = pyo.Constraint(
        model.hospitals, rule=nonempty_rule
    )

    model.total_hospitals = pyo.Objective(
        expr=sum(model.used[hospital] for hospital in model.hospitals),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_hospitals))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}