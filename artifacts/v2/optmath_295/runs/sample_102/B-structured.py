# IR: {"sets":{"employees":"0..7","projects":"0..7"},"params":{"employee_capacity":"nonnegative real[employees]","project_demand":"nonnegative real[projects]","cost_matrix":"real[employees,projects]","assignment_limit":"nonnegative real[employees,projects]"},"variables":{"hours":"nonnegative continuous[employees,projects]"},"constraints":["sum_j hours[i,j] <= employee_capacity[i] for each employee i","sum_i hours[i,j] == project_demand[j] for each project j","hours[i,j] <= assignment_limit[i,j] for each employee i and project j"],"objective":"minimize sum_i sum_j cost_matrix[i,j] * hours[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using indexed vectors and nested, row-major input matrices."""
    employee_capacity = params["employee_capacity"]
    project_demand = params["project_demand"]
    cost_matrix = params["cost_matrix"]
    assignment_limit = params["assignment_limit"]

    model = pyo.ConcreteModel()
    model.employees = pyo.RangeSet(0, 7)
    model.projects = pyo.RangeSet(0, 7)

    model.employee_capacity = pyo.Param(
        model.employees,
        initialize=lambda mdl, i: employee_capacity[i],
        within=pyo.NonNegativeReals,
    )
    model.project_demand = pyo.Param(
        model.projects,
        initialize=lambda mdl, j: project_demand[j],
        within=pyo.NonNegativeReals,
    )
    model.cost_matrix = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, i, j: cost_matrix[i][j],
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

    model.capacity_constraints = pyo.Constraint(
        model.employees,
        rule=lambda mdl, i: (
            sum(mdl.hours[i, j] for j in mdl.projects)
            <= mdl.employee_capacity[i]
        ),
    )
    model.demand_constraints = pyo.Constraint(
        model.projects,
        rule=lambda mdl, j: (
            sum(mdl.hours[i, j] for i in mdl.employees)
            == mdl.project_demand[j]
        ),
    )
    model.assignment_constraints = pyo.Constraint(
        model.employees,
        model.projects,
        rule=lambda mdl, i, j: (
            mdl.hours[i, j] <= mdl.assignment_limit[i, j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost_matrix[i, j] * model.hours[i, j]
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