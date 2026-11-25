# IR: {"sets":{"R":"0..6","F":"0..6"},"params":{"resource_weights":"nonnegative weight indexed by R, from params['resource_weights']","facility_capacity":"nonnegative scalar, from params['facility_capacity']"},"variables":{"assigned[r,f]":"binary for r in R, f in F","facility_used[f]":"binary for f in F"},"constraints":["For each r: sum_f assigned[r,f] = 1","For each f: sum_r resource_weights[r]*assigned[r,f] <= facility_capacity*facility_used[f]","For each r,f: assigned[r,f] <= facility_used[f]"],"objective":"minimize sum_f facility_used[f]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    resource_weights = params["resource_weights"]
    facility_capacity = params["facility_capacity"]

    model = pyo.ConcreteModel()
    model.resources = pyo.RangeSet(0, 6)
    model.facilities = pyo.RangeSet(0, 6)

    model.resource_weights = pyo.Param(
        model.resources,
        initialize={
            resource: resource_weights[resource]
            for resource in model.resources
        },
        within=pyo.NonNegativeReals,
    )
    model.facility_capacity = pyo.Param(
        initialize=facility_capacity,
        within=pyo.NonNegativeReals,
    )

    model.assigned = pyo.Var(
        model.resources, model.facilities, domain=pyo.Binary
    )
    model.facility_used = pyo.Var(model.facilities, domain=pyo.Binary)

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
        ) <= instance.facility_capacity * instance.facility_used[facility]

    model.capacity_constraints = pyo.Constraint(
        model.facilities, rule=capacity_rule
    )

    def usage_rule(instance, resource, facility):
        return (
            instance.assigned[resource, facility]
            <= instance.facility_used[facility]
        )

    model.usage_constraints = pyo.Constraint(
        model.resources, model.facilities, rule=usage_rule
    )

    model.total_facilities = pyo.Objective(
        expr=sum(
            model.facility_used[facility]
            for facility in model.facilities
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_facilities))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}