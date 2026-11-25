# IR: {"sets":{"resources":[0,1,2,3,4,5],"centers":[0,1,2,3,4,5]},"params":{"resource_weights":"params['resource_weights'], ordered sequence of six weights","center_capacity":"params['center_capacity']"},"variables":{"x[i,j]":"binary: resource i assigned to center j","y[j]":"binary: center j used"},"constraints":["For each i: sum_j x[i,j] = 1","For each i,j: x[i,j] <= y[j]","For each j: y[j] <= sum_i x[i,j]","For each j: sum_i resource_weights[i]*x[i,j] <= center_capacity*y[j]"],"objective":"minimize sum_j y[j]"}
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

    def assignment_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.centers) == 1

    model.assignment = pyo.Constraint(model.resources, rule=assignment_rule)

    def usage_link_rule(mdl, i, j):
        return mdl.x[i, j] <= mdl.y[j]

    model.usage_link = pyo.Constraint(
        model.resources, model.centers, rule=usage_link_rule
    )

    def nonempty_rule(mdl, j):
        return mdl.y[j] <= sum(mdl.x[i, j] for i in mdl.resources)

    model.nonempty = pyo.Constraint(model.centers, rule=nonempty_rule)

    def capacity_rule(mdl, j):
        return (
            sum(mdl.weights[i] * mdl.x[i, j] for i in mdl.resources)
            <= mdl.capacity * mdl.y[j]
        )

    model.capacity_limits = pyo.Constraint(model.centers, rule=capacity_rule)

    model.total_centers = pyo.Objective(
        expr=sum(model.y[j] for j in model.centers),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_centers))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}