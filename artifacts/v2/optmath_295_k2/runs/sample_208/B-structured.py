# IR: {"sets":{"resources":"0..6","facilities":"0..6"},"params":{"resource_weights":"nonnegative weight indexed by resource","facility_capacity":"nonnegative uniform capacity"},"variables":{"assigned[i,j]":"binary","used[j]":"binary"},"constraints":["forall i: sum_j assigned[i,j] = 1","forall j: sum_i resource_weights[i]*assigned[i,j] <= facility_capacity*used[j]","forall i,j: assigned[i,j] <= used[j]"],"objective":"minimize sum_j used[j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.resources = pyo.RangeSet(0, 6)
    model.facilities = pyo.RangeSet(0, 6)

    model.resource_weights = pyo.Param(
        model.resources,
        initialize={
            resource: params["resource_weights"][resource]
            for resource in model.resources
        },
        within=pyo.NonNegativeReals,
    )
    model.facility_capacity = pyo.Param(
        initialize=params["facility_capacity"],
        within=pyo.NonNegativeReals,
    )

    model.assigned = pyo.Var(
        model.resources, model.facilities, domain=pyo.Binary
    )
    model.used = pyo.Var(model.facilities, domain=pyo.Binary)

    def assignment_rule(instance, resource):
        return sum(
            instance.assigned[resource, facility]
            for facility in instance.facilities
        ) == 1

    model.assignment_constraints = pyo.Constraint(
        model.resources, rule=assignment_rule
    )

    def capacity_rule(instance, facility):
        return sum(
            instance.resource_weights[resource]
            * instance.assigned[resource, facility]
            for resource in instance.resources
        ) <= instance.facility_capacity * instance.used[facility]

    model.capacity_constraints = pyo.Constraint(
        model.facilities, rule=capacity_rule
    )

    def usage_rule(instance, resource, facility):
        return (
            instance.assigned[resource, facility]
            <= instance.used[facility]
        )

    model.usage_constraints = pyo.Constraint(
        model.resources, model.facilities, rule=usage_rule
    )

    model.total_facilities = pyo.Objective(
        expr=sum(model.used[facility] for facility in model.facilities),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_facilities))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}