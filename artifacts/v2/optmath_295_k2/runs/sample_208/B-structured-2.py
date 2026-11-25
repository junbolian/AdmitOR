# IR: {"sets":{"resources":"0..6","facilities":"0..6"},"params":{"resource_weights":"params['resource_weights'][i] for i in resources","facility_capacity":"params['facility_capacity']"},"variables":{"assigned[i,j]":"binary","facility_used[j]":"binary"},"constraints":["For each resource i: sum_j assigned[i,j] == 1","For each facility j: sum_i resource_weights[i]*assigned[i,j] <= facility_capacity*facility_used[j]","For each resource i and facility j: assigned[i,j] <= facility_used[j]"],"objective":"minimize sum_j facility_used[j]"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
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
        model.resources,
        model.facilities,
        domain=pyo.Binary,
    )
    model.facility_used = pyo.Var(
        model.facilities,
        domain=pyo.Binary,
    )

    def assignment_rule(mod, resource):
        return sum(
            mod.assigned[resource, facility]
            for facility in mod.facilities
        ) == 1

    model.assignment_constraints = pyo.Constraint(
        model.resources,
        rule=assignment_rule,
    )

    def capacity_rule(mod, facility):
        return sum(
            mod.resource_weights[resource] * mod.assigned[resource, facility]
            for resource in mod.resources
        ) <= mod.facility_capacity * mod.facility_used[facility]

    model.capacity_constraints = pyo.Constraint(
        model.facilities,
        rule=capacity_rule,
    )

    def usage_rule(mod, resource, facility):
        return mod.assigned[resource, facility] <= mod.facility_used[facility]

    model.usage_constraints = pyo.Constraint(
        model.resources,
        model.facilities,
        rule=usage_rule,
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
    except (ApplicationError, RuntimeError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_facilities))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}