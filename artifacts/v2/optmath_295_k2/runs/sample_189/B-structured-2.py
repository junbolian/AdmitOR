# IR: {"sets":{"I":[0,1,2,3],"J":[0,1,2,3,4]},"params":{"consultant_availability":"nonnegative[I]","project_requirements":"nonnegative[J]","cost_matrix":"real[I,J]","assignment_capacity":"nonnegative[I,J]"},"variables":{"hours[I,J]":"continuous nonnegative"},"constraints":["sum(hours[i,j] for j in J) <= consultant_availability[i] for i in I","sum(hours[i,j] for i in I) == project_requirements[j] for j in J","hours[i,j] <= assignment_capacity[i,j] for i in I, j in J"],"objective":"minimize sum(cost_matrix[i,j]*hours[i,j] for i in I, j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using vectors and nested matrices indexed by consultant/project."""
    model = pyo.ConcreteModel()

    model.consultants = pyo.RangeSet(0, 3)
    model.projects = pyo.RangeSet(0, 4)

    model.consultant_availability = pyo.Param(
        model.consultants,
        initialize={
            i: params["consultant_availability"][i]
            for i in model.consultants
        },
        within=pyo.NonNegativeReals,
    )
    model.project_requirements = pyo.Param(
        model.projects,
        initialize={
            j: params["project_requirements"][j]
            for j in model.projects
        },
        within=pyo.NonNegativeReals,
    )
    model.cost_matrix = pyo.Param(
        model.consultants,
        model.projects,
        initialize={
            (i, j): params["cost_matrix"][i][j]
            for i in model.consultants
            for j in model.projects
        },
        within=pyo.Reals,
    )
    model.assignment_capacity = pyo.Param(
        model.consultants,
        model.projects,
        initialize={
            (i, j): params["assignment_capacity"][i][j]
            for i in model.consultants
            for j in model.projects
        },
        within=pyo.NonNegativeReals,
    )

    model.hours = pyo.Var(
        model.consultants,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    def availability_rule(instance, i):
        return (
            sum(instance.hours[i, j] for j in instance.projects)
            <= instance.consultant_availability[i]
        )

    model.availability_limits = pyo.Constraint(
        model.consultants,
        rule=availability_rule,
    )

    def requirement_rule(instance, j):
        return (
            sum(instance.hours[i, j] for i in instance.consultants)
            == instance.project_requirements[j]
        )

    model.project_coverage = pyo.Constraint(
        model.projects,
        rule=requirement_rule,
    )

    def capacity_rule(instance, i, j):
        return (
            instance.hours[i, j]
            <= instance.assignment_capacity[i, j]
        )

    model.assignment_limits = pyo.Constraint(
        model.consultants,
        model.projects,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost_matrix[i, j] * model.hours[i, j]
            for i in model.consultants
            for j in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Propagate unrelated runtime errors.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}