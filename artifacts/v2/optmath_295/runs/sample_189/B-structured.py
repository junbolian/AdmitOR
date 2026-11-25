# IR: {"sets":{"I":[0,1,2,3],"J":[0,1,2,3,4]},"params":{"consultant_capacity":"I -> hours","project_requirement":"J -> hours","cost":"I x J -> cost/hour","assignment_capacity":"I x J -> hours"},"variables":{"hours[i,j]":"nonnegative continuous, i in I, j in J"},"constraints":["sum(j in J, hours[i,j]) <= consultant_capacity[i] for i in I","sum(i in I, hours[i,j]) >= project_requirement[j] for j in J","hours[i,j] <= assignment_capacity[i][j] for i in I, j in J"],"objective":"minimize sum(i in I, j in J, cost[i][j] * hours[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 3)
    model.J = pyo.RangeSet(0, 4)

    model.consultant_capacity = pyo.Param(
        model.I,
        initialize={
            i: params["consultant_capacity"][i]
            for i in model.I
        },
    )
    model.project_requirement = pyo.Param(
        model.J,
        initialize={
            j: params["project_requirement"][j]
            for j in model.J
        },
    )
    model.cost = pyo.Param(
        model.I,
        model.J,
        initialize={
            (i, j): params["cost"][i][j]
            for i in model.I
            for j in model.J
        },
    )
    model.assignment_capacity = pyo.Param(
        model.I,
        model.J,
        initialize={
            (i, j): params["assignment_capacity"][i][j]
            for i in model.I
            for j in model.J
        },
    )

    model.hours = pyo.Var(
        model.I,
        model.J,
        domain=pyo.NonNegativeReals,
    )

    def consultant_capacity_rule(instance, i):
        return (
            sum(instance.hours[i, j] for j in instance.J)
            <= instance.consultant_capacity[i]
        )

    model.consultant_limits = pyo.Constraint(
        model.I,
        rule=consultant_capacity_rule,
    )

    def project_requirement_rule(instance, j):
        return (
            sum(instance.hours[i, j] for i in instance.I)
            >= instance.project_requirement[j]
        )

    model.project_requirements = pyo.Constraint(
        model.J,
        rule=project_requirement_rule,
    )

    def assignment_capacity_rule(instance, i, j):
        return (
            instance.hours[i, j]
            <= instance.assignment_capacity[i, j]
        )

    model.assignment_limits = pyo.Constraint(
        model.I,
        model.J,
        rule=assignment_capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.hours[i, j]
            for i in model.I
            for j in model.J
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}