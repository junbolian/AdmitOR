# IR: {"sets":{"employees":[0,1,2,3,4],"projects":[0,1,2,3,4]},"params":{"assignment_cost":"real[employees,projects]","employee_total_capacity":"nonnegative_real[employees]","employee_project_limit":"nonnegative_real[employees,projects]","project_demand":"nonnegative_real[projects]"},"variables":{"assigned_units":"nonnegative_real[employees,projects]"},"constraints":["forall i: sum_j assigned_units[i,j] == employee_total_capacity[i]","forall j: sum_i assigned_units[i,j] == project_demand[j]","forall i,j: assigned_units[i,j] <= employee_project_limit[i,j]"],"objective":"minimize sum_i sum_j assignment_cost[i,j] * assigned_units[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.employees = pyo.RangeSet(0, 4)
    model.projects = pyo.RangeSet(0, 4)

    model.assignment_cost = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, i, j: params["assignment_cost"][i][j],
        within=pyo.Reals,
    )
    model.employee_total_capacity = pyo.Param(
        model.employees,
        initialize=lambda mdl, i: params["employee_total_capacity"][i],
        within=pyo.NonNegativeReals,
    )
    model.employee_project_limit = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, i, j: params["employee_project_limit"][i][j],
        within=pyo.NonNegativeReals,
    )
    model.project_demand = pyo.Param(
        model.projects,
        initialize=lambda mdl, j: params["project_demand"][j],
        within=pyo.NonNegativeReals,
    )

    model.assigned_units = pyo.Var(
        model.employees,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    model.employee_capacity_balance = pyo.Constraint(
        model.employees,
        rule=lambda mdl, i: (
            sum(mdl.assigned_units[i, j] for j in mdl.projects)
            == mdl.employee_total_capacity[i]
        ),
    )
    model.project_demand_balance = pyo.Constraint(
        model.projects,
        rule=lambda mdl, j: (
            sum(mdl.assigned_units[i, j] for i in mdl.employees)
            == mdl.project_demand[j]
        ),
    )
    model.pair_assignment_limit = pyo.Constraint(
        model.employees,
        model.projects,
        rule=lambda mdl, i, j: (
            mdl.assigned_units[i, j] <= mdl.employee_project_limit[i, j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[i, j] * model.assigned_units[i, j]
            for i in model.employees
            for j in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}