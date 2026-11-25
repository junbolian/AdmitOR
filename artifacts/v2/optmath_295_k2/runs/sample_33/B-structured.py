# IR: {"sets":{"employees":"0..5","projects":"0..6"},"params":{"employee_availability":"nonnegative[6]","project_requirement":"nonnegative[7]","assignment_cost":"real[6][7] or flat real[42], employee-major","assignment_limit":"nonnegative[6][7] or flat nonnegative[42], employee-major"},"variables":{"hours[i,j]":"continuous nonnegative"},"constraints":["sum_j hours[i,j] <= employee_availability[i] for each employee i","sum_i hours[i,j] >= project_requirement[j] for each project j","hours[i,j] <= assignment_limit[i,j] for each employee i and project j"],"objective":"minimize sum_i sum_j assignment_cost[i,j]*hours[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    employee_availability = params["employee_availability"]
    project_requirement = params["project_requirement"]
    assignment_cost = params["assignment_cost"]
    assignment_limit = params["assignment_limit"]

    def pair_value(values, employee, project):
        if len(values) == 6:
            return values[employee][project]
        return values[7 * employee + project]

    model = pyo.ConcreteModel()
    model.employees = pyo.RangeSet(0, 5)
    model.projects = pyo.RangeSet(0, 6)

    model.available_hours = pyo.Param(
        model.employees,
        initialize=lambda mdl, i: employee_availability[i],
        within=pyo.NonNegativeReals,
    )
    model.required_hours = pyo.Param(
        model.projects,
        initialize=lambda mdl, j: project_requirement[j],
        within=pyo.NonNegativeReals,
    )
    model.hourly_cost = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, i, j: pair_value(assignment_cost, i, j),
        within=pyo.Reals,
    )
    model.pair_limit = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, i, j: pair_value(assignment_limit, i, j),
        within=pyo.NonNegativeReals,
    )

    model.hours = pyo.Var(
        model.employees,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    model.employee_capacity = pyo.Constraint(
        model.employees,
        rule=lambda mdl, i: sum(mdl.hours[i, j] for j in mdl.projects)
        <= mdl.available_hours[i],
    )
    model.project_demand = pyo.Constraint(
        model.projects,
        rule=lambda mdl, j: sum(mdl.hours[i, j] for i in mdl.employees)
        >= mdl.required_hours[j],
    )
    model.assignment_capacity = pyo.Constraint(
        model.employees,
        model.projects,
        rule=lambda mdl, i, j: mdl.hours[i, j] <= mdl.pair_limit[i, j],
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.hourly_cost[i, j] * model.hours[i, j]
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