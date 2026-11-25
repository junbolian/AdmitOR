# IR: {"sets":{"employees":"0..7","projects":"0..8"},"params":{"employee_availability":"nonnegative real[employees]","project_requirements":"nonnegative real[projects]","assignment_cost":"real[employees,projects]","assignment_capacity":"nonnegative real[employees,projects]"},"variables":{"hours":"continuous nonnegative real[employees,projects]"},"constraints":["sum(hours[i,j] for j in projects) <= employee_availability[i] for each employee i","sum(hours[i,j] for i in employees) == project_requirements[j] for each project j","hours[i,j] <= assignment_capacity[i,j] for each employee-project pair"],"objective":"minimize sum(assignment_cost[i,j]*hours[i,j] for all employee-project pairs)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using indexed sequences or integer-keyed nested mappings."""
    model = pyo.ConcreteModel()

    model.employees = pyo.RangeSet(0, 7)
    model.projects = pyo.RangeSet(0, 8)

    model.employee_availability = pyo.Param(
        model.employees,
        initialize={
            i: params["employee_availability"][i]
            for i in model.employees
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
    model.assignment_cost = pyo.Param(
        model.employees,
        model.projects,
        initialize={
            (i, j): params["assignment_cost"][i][j]
            for i in model.employees
            for j in model.projects
        },
        within=pyo.Reals,
    )
    model.assignment_capacity = pyo.Param(
        model.employees,
        model.projects,
        initialize={
            (i, j): params["assignment_capacity"][i][j]
            for i in model.employees
            for j in model.projects
        },
        within=pyo.NonNegativeReals,
    )

    model.hours = pyo.Var(
        model.employees,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    def availability_rule(model, i):
        return (
            sum(model.hours[i, j] for j in model.projects)
            <= model.employee_availability[i]
        )

    model.availability_limits = pyo.Constraint(
        model.employees, rule=availability_rule
    )

    def requirement_rule(model, j):
        return (
            sum(model.hours[i, j] for i in model.employees)
            == model.project_requirements[j]
        )

    model.project_balances = pyo.Constraint(
        model.projects, rule=requirement_rule
    )

    def capacity_rule(model, i, j):
        return model.hours[i, j] <= model.assignment_capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.employees, model.projects, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[i, j] * model.hours[i, j]
            for i in model.employees
            for j in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}