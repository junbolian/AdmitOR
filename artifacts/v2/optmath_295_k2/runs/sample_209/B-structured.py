# IR: {"sets":{"persons":"0..6","projects":"0..6"},"params":{"person_availability":"nonnegative[persons]","project_requirement":"nonnegative[projects]","assignment_cost":"real[persons,projects]","assignment_upper_limit":"nonnegative[persons,projects]"},"variables":{"hours":"continuous nonnegative[persons,projects]"},"constraints":["sum(hours[i,j] for j in projects) <= person_availability[i] for each i in persons","sum(hours[i,j] for i in persons) == project_requirement[j] for each j in projects","hours[i,j] <= assignment_upper_limit[i,j] for each (i,j)"],"objective":"minimize sum(assignment_cost[i,j] * hours[i,j] for each (i,j))"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.persons = pyo.RangeSet(0, 6)
    model.projects = pyo.RangeSet(0, 6)

    model.person_availability = pyo.Param(
        model.persons,
        initialize=lambda model, i: params["person_availability"][i],
        within=pyo.NonNegativeReals,
    )
    model.project_requirement = pyo.Param(
        model.projects,
        initialize=lambda model, j: params["project_requirement"][j],
        within=pyo.NonNegativeReals,
    )
    model.assignment_cost = pyo.Param(
        model.persons,
        model.projects,
        initialize=lambda model, i, j: params["assignment_cost"][i][j],
        within=pyo.Reals,
    )
    model.assignment_upper_limit = pyo.Param(
        model.persons,
        model.projects,
        initialize=lambda model, i, j: params["assignment_upper_limit"][i][j],
        within=pyo.NonNegativeReals,
    )

    model.hours = pyo.Var(
        model.persons,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    model.availability_constraints = pyo.Constraint(
        model.persons,
        rule=lambda model, i: (
            sum(model.hours[i, j] for j in model.projects)
            <= model.person_availability[i]
        ),
    )

    model.requirement_constraints = pyo.Constraint(
        model.projects,
        rule=lambda model, j: (
            sum(model.hours[i, j] for i in model.persons)
            == model.project_requirement[j]
        ),
    )

    model.assignment_limit_constraints = pyo.Constraint(
        model.persons,
        model.projects,
        rule=lambda model, i, j: (
            model.hours[i, j] <= model.assignment_upper_limit[i, j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[i, j] * model.hours[i, j]
            for i in model.persons
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