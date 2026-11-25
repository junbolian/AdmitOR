# IR: {"sets":{"employees":"0..5","projects":"0..6"},"params":{"employee_availability":"params['employee_availability'][i]","project_requirements":"params['project_requirements'][j]","assignment_cost":"params['assignment_cost'][i][j]","assignment_limit":"params['assignment_limit'][i][j]"},"variables":{"hours[i,j]":"continuous, nonnegative"},"constraints":{"employee_capacity":"sum_j hours[i,j] <= employee_availability[i] for each i","project_demand":"sum_i hours[i,j] >= project_requirements[j] for each j","assignment_cap":"hours[i,j] <= assignment_limit[i,j] for each i,j"},"objective":"minimize sum_i sum_j assignment_cost[i,j] * hours[i,j]"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    employee_availability = params["employee_availability"]
    project_requirements = params["project_requirements"]
    assignment_cost = params["assignment_cost"]
    assignment_limit = params["assignment_limit"]

    model = pyo.ConcreteModel()

    model.employees = pyo.RangeSet(0, 5)
    model.projects = pyo.RangeSet(0, 6)

    model.employee_availability = pyo.Param(
        model.employees,
        initialize=lambda mdl, i: employee_availability[i],
        within=pyo.NonNegativeReals,
    )
    model.project_requirements = pyo.Param(
        model.projects,
        initialize=lambda mdl, j: project_requirements[j],
        within=pyo.NonNegativeReals,
    )
    model.assignment_cost = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, i, j: assignment_cost[i][j],
        within=pyo.Reals,
    )
    model.assignment_limit = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, i, j: assignment_limit[i][j],
        within=pyo.NonNegativeReals,
    )

    model.hours = pyo.Var(
        model.employees,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    model.employee_capacity = pyo.Constraint(
        model.employees,
        rule=lambda mdl, i: (
            sum(mdl.hours[i, j] for j in mdl.projects)
            <= mdl.employee_availability[i]
        ),
    )
    model.project_demand = pyo.Constraint(
        model.projects,
        rule=lambda mdl, j: (
            sum(mdl.hours[i, j] for i in mdl.employees)
            >= mdl.project_requirements[j]
        ),
    )
    model.assignment_cap = pyo.Constraint(
        model.employees,
        model.projects,
        rule=lambda mdl, i, j: (
            mdl.hours[i, j] <= mdl.assignment_limit[i, j]
        ),
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
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}