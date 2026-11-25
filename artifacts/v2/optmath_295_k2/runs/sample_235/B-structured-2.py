# IR: {"sets":{"employees":"0..5","projects":"0..5"},"params":{"employee_availability":"nonnegative real[employees]","project_requirement":"nonnegative real[projects]","assignment_cost":"real[employees,projects]","assignment_capacity":"nonnegative real[employees,projects]"},"variables":{"hours":"nonnegative real[employees,projects]"},"constraints":["sum_j hours[i,j] = employee_availability[i] for each employee i","sum_i hours[i,j] = project_requirement[j] for each project j","hours[i,j] <= assignment_capacity[i,j] for each employee i and project j"],"objective":"minimize sum_i sum_j assignment_cost[i,j] * hours[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.employees = pyo.RangeSet(0, 5)
    model.projects = pyo.RangeSet(0, 5)

    model.employee_availability = pyo.Param(
        model.employees,
        initialize={
            i: params["employee_availability"][i]
            for i in model.employees
        },
        within=pyo.NonNegativeReals,
    )
    model.project_requirement = pyo.Param(
        model.projects,
        initialize={
            j: params["project_requirement"][j]
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

    def employee_balance_rule(mdl, i):
        return (
            sum(mdl.hours[i, j] for j in mdl.projects)
            == mdl.employee_availability[i]
        )

    model.employee_balance = pyo.Constraint(
        model.employees,
        rule=employee_balance_rule,
    )

    def project_balance_rule(mdl, j):
        return (
            sum(mdl.hours[i, j] for i in mdl.employees)
            == mdl.project_requirement[j]
        )

    model.project_balance = pyo.Constraint(
        model.projects,
        rule=project_balance_rule,
    )

    def capacity_limit_rule(mdl, i, j):
        return mdl.hours[i, j] <= mdl.assignment_capacity[i, j]

    model.capacity_limit = pyo.Constraint(
        model.employees,
        model.projects,
        rule=capacity_limit_rule,
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
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}