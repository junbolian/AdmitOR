# IR: {"sets":{"employees":"0..5","projects":"0..4"},"params":{"employee_supply":"params['employee_supply'][i]","project_demand":"params['project_demand'][j]","cost":"params['cost'][i][j]","assignment_capacity":"params['assignment_capacity'][i][j]"},"variables":{"hours[i,j]":"nonnegative continuous"},"constraints":["sum_j hours[i,j] == employee_supply[i] for each employee i","sum_i hours[i,j] == project_demand[j] for each project j","hours[i,j] <= assignment_capacity[i,j] for each employee-project pair"],"objective":"minimize sum_i sum_j cost[i,j] * hours[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.employees = pyo.RangeSet(0, 5)
    model.projects = pyo.RangeSet(0, 4)

    model.employee_supply = pyo.Param(
        model.employees,
        initialize={
            i: params["employee_supply"][i]
            for i in model.employees
        },
        within=pyo.NonNegativeReals,
    )
    model.project_demand = pyo.Param(
        model.projects,
        initialize={
            j: params["project_demand"][j]
            for j in model.projects
        },
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.employees,
        model.projects,
        initialize={
            (i, j): params["cost"][i][j]
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

    def employee_balance_rule(instance, i):
        return (
            sum(instance.hours[i, j] for j in instance.projects)
            == instance.employee_supply[i]
        )

    model.employee_balance = pyo.Constraint(
        model.employees,
        rule=employee_balance_rule,
    )

    def project_balance_rule(instance, j):
        return (
            sum(instance.hours[i, j] for i in instance.employees)
            == instance.project_demand[j]
        )

    model.project_balance = pyo.Constraint(
        model.projects,
        rule=project_balance_rule,
    )

    def capacity_limit_rule(instance, i, j):
        return (
            instance.hours[i, j]
            <= instance.assignment_capacity[i, j]
        )

    model.capacity_limit = pyo.Constraint(
        model.employees,
        model.projects,
        rule=capacity_limit_rule,
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
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}