# IR: {"sets":{"E":"0..7","P":"0..8"},"params":{"employee_availability":"nonnegative hours[E]","project_requirements":"nonnegative hours[P]","assignment_costs":"real cost per hour[E,P]","pair_capacities":"nonnegative hours[E,P]"},"variables":{"hours[E,P]":"continuous nonnegative"},"constraints":["sum(hours[i,j] for j in P) <= employee_availability[i] for i in E","sum(hours[i,j] for i in E) == project_requirements[j] for j in P","hours[i,j] <= pair_capacities[i,j] for i in E, j in P"],"objective":"minimize sum(assignment_costs[i,j] * hours[i,j] for i in E, j in P)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.employees = pyo.RangeSet(0, 7)
    model.projects = pyo.RangeSet(0, 8)

    model.employee_availability = pyo.Param(
        model.employees,
        initialize={
            i: params["employee_availability"][i]
            for i in model.employees
        },
        within=pyo.NonNegativeReals,
    )
    model.project_requirements = pyo.Param(
        model.projects,
        initialize={
            j: params["project_requirements"][j]
            for j in model.projects
        },
        within=pyo.NonNegativeReals,
    )
    model.assignment_costs = pyo.Param(
        model.employees,
        model.projects,
        initialize={
            (i, j): params["assignment_costs"][i][j]
            for i in model.employees
            for j in model.projects
        },
        within=pyo.Reals,
    )
    model.pair_capacities = pyo.Param(
        model.employees,
        model.projects,
        initialize={
            (i, j): params["pair_capacities"][i][j]
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

    def availability_rule(current_model, i):
        return (
            sum(current_model.hours[i, j] for j in current_model.projects)
            <= current_model.employee_availability[i]
        )

    model.availability_constraints = pyo.Constraint(
        model.employees,
        rule=availability_rule,
    )

    def requirement_rule(current_model, j):
        return (
            sum(current_model.hours[i, j] for i in current_model.employees)
            == current_model.project_requirements[j]
        )

    model.requirement_constraints = pyo.Constraint(
        model.projects,
        rule=requirement_rule,
    )

    def capacity_rule(current_model, i, j):
        return (
            current_model.hours[i, j]
            <= current_model.pair_capacities[i, j]
        )

    model.capacity_constraints = pyo.Constraint(
        model.employees,
        model.projects,
        rule=capacity_rule,
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
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}