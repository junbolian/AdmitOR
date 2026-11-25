# IR: {"sets":{"employees":"0..5","projects":"0..4"},"params":{"employee_supply":"nonnegative[employees], from params","project_demand":"nonnegative[projects], from params","cost":"real[employees,projects], from params (row-major)","assignment_capacity":"nonnegative[employees,projects], from params (row-major)"},"variables":{"hours":"continuous nonnegative[employees,projects]"},"constraints":["For each employee i: sum_j hours[i,j] = employee_supply[i]","For each project j: sum_i hours[i,j] = project_demand[j]","For each employee-project pair (i,j): hours[i,j] <= assignment_capacity[i,j]"],"objective":"minimize sum_i sum_j cost[i,j] * hours[i,j]"}
import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.employees = pyo.RangeSet(0, 5)
    model.projects = pyo.RangeSet(0, 4)

    model.employee_supply = pyo.Param(
        model.employees,
        initialize=lambda mdl, i: params["employee_supply"][i],
        within=pyo.NonNegativeReals,
    )
    model.project_demand = pyo.Param(
        model.projects,
        initialize=lambda mdl, j: params["project_demand"][j],
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, i, j: params["cost"][i][j],
        within=pyo.Reals,
    )
    model.assignment_capacity = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, i, j: params["assignment_capacity"][i][j],
        within=pyo.NonNegativeReals,
    )

    model.hours = pyo.Var(
        model.employees,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    def employee_hours_rule(mdl, i):
        return (
            sum(mdl.hours[i, j] for j in mdl.projects)
            == mdl.employee_supply[i]
        )

    model.employee_hours = pyo.Constraint(
        model.employees,
        rule=employee_hours_rule,
    )

    def project_hours_rule(mdl, j):
        return (
            sum(mdl.hours[i, j] for i in mdl.employees)
            == mdl.project_demand[j]
        )

    model.project_hours = pyo.Constraint(
        model.projects,
        rule=project_hours_rule,
    )

    def capacity_rule(mdl, i, j):
        return mdl.hours[i, j] <= mdl.assignment_capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.employees,
        model.projects,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.hours[i, j]
            for i in model.employees
            for j in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}