# IR: {"sets":{"employees":[0,1,2,3,4],"projects":[0,1,2,3,4]},"params":{"employee_availability":"params['employee_availability'][i]","project_requirement":"params['project_requirement'][j]","assignment_cost":"params['assignment_cost'][i][j]","assignment_limit":"params['assignment_limit'][i][j]"},"variables":{"hours[i,j]":"continuous, nonnegative"},"constraints":["sum_j hours[i,j] <= employee_availability[i] for each employee i","sum_i hours[i,j] == project_requirement[j] for each project j","hours[i,j] <= assignment_limit[i,j] for each employee i and project j"],"objective":"minimize sum_i sum_j assignment_cost[i,j] * hours[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.employees = pyo.RangeSet(0, 4)
    model.projects = pyo.RangeSet(0, 4)

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

    model.assignment_limit = pyo.Param(
        model.employees,
        model.projects,
        initialize={
            (i, j): params["assignment_limit"][i][j]
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

    def availability_rule(instance, i):
        return (
            sum(instance.hours[i, j] for j in instance.projects)
            <= instance.employee_availability[i]
        )

    model.availability_constraints = pyo.Constraint(
        model.employees,
        rule=availability_rule,
    )

    def requirement_rule(instance, j):
        return (
            sum(instance.hours[i, j] for i in instance.employees)
            == instance.project_requirement[j]
        )

    model.requirement_constraints = pyo.Constraint(
        model.projects,
        rule=requirement_rule,
    )

    def assignment_limit_rule(instance, i, j):
        return instance.hours[i, j] <= instance.assignment_limit[i, j]

    model.assignment_limit_constraints = pyo.Constraint(
        model.employees,
        model.projects,
        rule=assignment_limit_rule,
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
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}