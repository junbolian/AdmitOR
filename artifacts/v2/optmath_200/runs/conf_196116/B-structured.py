# IR: {"sets":{"I":"0..6","J":"0..7"},"params":{"employee_availability":"a[i]","project_requirements":"r[j]","assignment_cost":"c[i,j]","assignment_limit":"u[i,j]"},"variables":{"x[i,j]":"nonnegative continuous hours"},"constraints":["sum(j in J, x[i,j]) = a[i] for each i in I","sum(i in I, x[i,j]) = r[j] for each j in J","x[i,j] <= u[i,j] for each (i,j) in I x J"],"objective":"minimize sum(i in I, j in J, c[i,j]*x[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["employee_availability"]
    requirements = params["project_requirements"]
    costs = params["assignment_cost"]
    limits = params["assignment_limit"]

    # Accept either nested 7-by-8 matrices or flattened row-major arrays.
    def matrix_entry(data, employee, project):
        if len(data) == 7 * 8:
            return data[employee * 8 + project]
        return data[employee][project]

    model = pyo.ConcreteModel()
    model.employees = pyo.RangeSet(0, 6)
    model.projects = pyo.RangeSet(0, 7)

    model.employee_availability = pyo.Param(
        model.employees,
        initialize=lambda mdl, i: availability[i],
    )
    model.project_requirements = pyo.Param(
        model.projects,
        initialize=lambda mdl, j: requirements[j],
    )
    model.assignment_cost = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, i, j: matrix_entry(costs, i, j),
    )
    model.assignment_limit = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, i, j: matrix_entry(limits, i, j),
    )

    model.hours = pyo.Var(
        model.employees, model.projects, domain=pyo.NonNegativeReals
    )

    model.employee_balance = pyo.Constraint(
        model.employees,
        rule=lambda mdl, i: sum(mdl.hours[i, j] for j in mdl.projects)
        == mdl.employee_availability[i],
    )
    model.project_balance = pyo.Constraint(
        model.projects,
        rule=lambda mdl, j: sum(mdl.hours[i, j] for i in mdl.employees)
        == mdl.project_requirements[j],
    )
    model.assignment_capacity = pyo.Constraint(
        model.employees,
        model.projects,
        rule=lambda mdl, i, j: mdl.hours[i, j] <= mdl.assignment_limit[i, j],
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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}