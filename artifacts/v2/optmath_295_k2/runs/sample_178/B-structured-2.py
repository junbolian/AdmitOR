# IR: {"sets":{"supplies":"0..6","hospitals":"0..6"},"params":{"supply_weights":"params['supply_weights'][i] for each supply i","hospital_capacity":"params['hospital_capacity']"},"variables":{"assigned[i,h]":"Binary","used[h]":"Binary"},"constraints":["For each supply i: sum_h assigned[i,h] = 1","For each hospital h: sum_i supply_weights[i]*assigned[i,h] <= hospital_capacity*used[h]","For each supply i and hospital h: assigned[i,h] <= used[h]","For each hospital h: used[h] <= sum_i assigned[i,h]"],"objective":"Minimize sum_h used[h]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.supplies = pyo.RangeSet(0, 6)
    model.hospitals = pyo.RangeSet(0, 6)

    model.supply_weights = pyo.Param(
        model.supplies,
        initialize={
            supply: params["supply_weights"][supply]
            for supply in model.supplies
        },
        within=pyo.NonNegativeReals,
    )
    model.hospital_capacity = pyo.Param(
        initialize=params["hospital_capacity"],
        within=pyo.NonNegativeReals,
    )

    model.assigned = pyo.Var(
        model.supplies, model.hospitals, domain=pyo.Binary
    )
    model.used = pyo.Var(model.hospitals, domain=pyo.Binary)

    def assignment_rule(instance, supply):
        return sum(
            instance.assigned[supply, hospital]
            for hospital in instance.hospitals
        ) == 1

    model.assignment_constraints = pyo.Constraint(
        model.supplies, rule=assignment_rule
    )

    def capacity_rule(instance, hospital):
        return sum(
            instance.supply_weights[supply]
            * instance.assigned[supply, hospital]
            for supply in instance.supplies
        ) <= instance.hospital_capacity * instance.used[hospital]

    model.capacity_constraints = pyo.Constraint(
        model.hospitals, rule=capacity_rule
    )

    def usage_link_rule(instance, supply, hospital):
        return instance.assigned[supply, hospital] <= instance.used[hospital]

    model.usage_link_constraints = pyo.Constraint(
        model.supplies, model.hospitals, rule=usage_link_rule
    )

    def nonempty_rule(instance, hospital):
        return instance.used[hospital] <= sum(
            instance.assigned[supply, hospital]
            for supply in instance.supplies
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
        # HiGHS can raise when no feasible solution is available to load.
        # Determine success below solely by objective-value retrieval.
        pass

    try:
        obj_val = float(pyo.value(model.total_hospitals))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}