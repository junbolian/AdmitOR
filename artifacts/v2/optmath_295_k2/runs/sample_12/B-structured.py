# IR: {"sets":{"I":"0..7","J":"0..8"},"params":{"employee_availability":"a[i], read from params","project_requirements":"r[j], read from params","assignment_costs":"c[i,j], read from params; cost per hour","pair_capacities":"u[i,j], read from params"},"variables":{"hours[i,j]":"continuous nonnegative"},"constraints":["sum(j in J, hours[i,j]) <= a[i] for each i in I","sum(i in I, hours[i,j]) == r[j] for each j in J","hours[i,j] <= u[i,j] for each (i,j) in I x J"],"objective":"minimize sum(i in I, j in J, c[i,j] * hours[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["employee_availability"]
    requirements = params["project_requirements"]
    costs = params["assignment_costs"]
    capacities = params["pair_capacities"]

    model = pyo.ConcreteModel()

    model.employees = pyo.RangeSet(0, 7)
    model.projects = pyo.RangeSet(0, 8)

    model.employee_availability = pyo.Param(
        model.employees,
        initialize={i: availability[i] for i in model.employees},
        within=pyo.NonNegativeReals,
    )
    model.project_requirements = pyo.Param(
        model.projects,
        initialize={j: requirements[j] for j in model.projects},
        within=pyo.NonNegativeReals,
    )
    model.assignment_costs = pyo.Param(
        model.employees,
        model.projects,
        initialize={
            (i, j): costs[i][j]
            for i in model.employees
            for j in model.projects
        },
        within=pyo.Reals,
    )
    model.pair_capacities = pyo.Param(
        model.employees,
        model.projects,
        initialize={
            (i, j): capacities[i][j]
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

    model.availability_limits = pyo.Constraint(
        model.employees, rule=availability_rule
    )

    def requirement_rule(instance, j):
        return (
            sum(instance.hours[i, j] for i in instance.employees)
            == instance.project_requirements[j]
        )

    model.requirement_balances = pyo.Constraint(
        model.projects, rule=requirement_rule
    )

    def capacity_rule(instance, i, j):
        return instance.hours[i, j] <= instance.pair_capacities[i, j]

    model.pair_limits = pyo.Constraint(
        model.employees, model.projects, rule=capacity_rule
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
    except RuntimeError as error:
        # APPsi raises this when it cannot load a feasible solution.
        # Let unexpected solver errors propagate.
        if "A feasible solution was not found" not in str(error):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}