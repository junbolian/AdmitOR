# IR: {"sets":{"employees":"0..6","projects":"0..6"},"params":{"employee_availability":"hours[employees]","project_requirements":"hours[projects]","assignment_costs":"cost_per_hour[employees,projects]","capacity_limits":"hours[employees,projects]"},"variables":{"hours[i,j]":"nonnegative continuous"},"constraints":["For each employee i: sum_j hours[i,j] = employee_availability[i]","For each project j: sum_i hours[i,j] = project_requirements[j]","For each pair (i,j): hours[i,j] <= capacity_limits[i,j]"],"objective":"minimize sum_i sum_j assignment_costs[i,j] * hours[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    employee_availability = params["employee_availability"]
    project_requirements = params["project_requirements"]
    assignment_costs = params["assignment_costs"]
    capacity_limits = params["capacity_limits"]

    model = pyo.ConcreteModel()
    model.employees = pyo.RangeSet(0, 6)
    model.projects = pyo.RangeSet(0, 6)

    model.employee_availability = pyo.Param(
        model.employees,
        initialize=lambda mdl, i: employee_availability[i],
    )
    model.project_requirements = pyo.Param(
        model.projects,
        initialize=lambda mdl, j: project_requirements[j],
    )
    model.assignment_costs = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, i, j: assignment_costs[i][j],
    )
    model.capacity_limits = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, i, j: capacity_limits[i][j],
    )

    model.hours = pyo.Var(
        model.employees,
        model.projects,
        domain=pyo.NonNegativeReals,
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
        rule=lambda mdl, i, j: mdl.hours[i, j] <= mdl.capacity_limits[i, j],
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_costs[i, j] * model.hours[i, j]
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