# IR: {"sets":{"resources":"0..5","centers":"0..5"},"params":{"resource_weights":"six resource weights","center_capacity":"uniform center capacity"},"variables":{"x[i,j]":"binary; resource i assigned to center j","y[j]":"binary; center j used"},"constraints":["For each i: sum_j x[i,j] = 1","For each j: sum_i resource_weights[i]*x[i,j] <= center_capacity*y[j]","For each i,j: x[i,j] <= y[j]","For each j: y[j] <= sum_i x[i,j]"],"objective":"minimize sum_j y[j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    resource_weights = params["resource_weights"]
    center_capacity = params["center_capacity"]

    model = pyo.ConcreteModel()
    model.resources = pyo.RangeSet(0, 5)
    model.centers = pyo.RangeSet(0, 5)

    model.weights = pyo.Param(
        model.resources,
        initialize={i: resource_weights[i] for i in model.resources},
    )
    model.capacity = pyo.Param(initialize=center_capacity)

    model.x = pyo.Var(model.resources, model.centers, domain=pyo.Binary)
    model.y = pyo.Var(model.centers, domain=pyo.Binary)

    def assignment_rule(instance, i):
        return sum(instance.x[i, j] for j in instance.centers) == 1

    model.assignment_constraints = pyo.Constraint(
        model.resources, rule=assignment_rule
    )

    def capacity_rule(instance, j):
        return (
            sum(
                instance.weights[i] * instance.x[i, j]
                for i in instance.resources
            )
            <= instance.capacity * instance.y[j]
        )

    model.capacity_constraints = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    def assignment_link_rule(instance, i, j):
        return instance.x[i, j] <= instance.y[j]

    model.assignment_links = pyo.Constraint(
        model.resources, model.centers, rule=assignment_link_rule
    )

    def used_center_rule(instance, j):
        return instance.y[j] <= sum(
            instance.x[i, j] for i in instance.resources
        )

    model.used_center_constraints = pyo.Constraint(
        model.centers, rule=used_center_rule
    )

    model.total_centers = pyo.Objective(
        expr=sum(model.y[j] for j in model.centers),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_centers))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}