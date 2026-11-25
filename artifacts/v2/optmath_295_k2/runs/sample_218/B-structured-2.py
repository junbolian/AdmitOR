# IR: {"sets":{"I":"0..6","J":"0..5"},"params":{"consultant_availability":"A[i]","project_requirements":"R[j]","assignment_cost":"C[i,j]","assignment_limits":"L[i,j]"},"variables":{"x[i,j]":{"type":"continuous","lower_bound":0}},"constraints":["sum(j in J, x[i,j]) <= A[i] for i in I","sum(i in I, x[i,j]) == R[j] for j in J","x[i,j] <= L[i,j] for i in I, j in J"],"objective":{"sense":"minimize","expression":"sum(i in I, j in J, C[i,j]*x[i,j])"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept indexed sequences or integer-keyed mappings; matrices use [i][j]."""
    availability = params["consultant_availability"]
    requirements = params["project_requirements"]
    costs = params["assignment_cost"]
    limits = params["assignment_limits"]

    model = pyo.ConcreteModel()

    model.consultants = pyo.RangeSet(0, 6)
    model.projects = pyo.RangeSet(0, 5)

    model.consultant_availability = pyo.Param(
        model.consultants,
        initialize=lambda mdl, i: availability[i],
        within=pyo.NonNegativeReals,
    )
    model.project_requirements = pyo.Param(
        model.projects,
        initialize=lambda mdl, j: requirements[j],
        within=pyo.NonNegativeReals,
    )
    model.assignment_cost = pyo.Param(
        model.consultants,
        model.projects,
        initialize=lambda mdl, i, j: costs[i][j],
        within=pyo.Reals,
    )
    model.assignment_limits = pyo.Param(
        model.consultants,
        model.projects,
        initialize=lambda mdl, i, j: limits[i][j],
        within=pyo.NonNegativeReals,
    )

    model.hours = pyo.Var(
        model.consultants,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    model.availability_constraints = pyo.Constraint(
        model.consultants,
        rule=lambda mdl, i: sum(
            mdl.hours[i, j] for j in mdl.projects
        ) <= mdl.consultant_availability[i],
    )

    model.requirement_constraints = pyo.Constraint(
        model.projects,
        rule=lambda mdl, j: sum(
            mdl.hours[i, j] for i in mdl.consultants
        ) == mdl.project_requirements[j],
    )

    model.assignment_limit_constraints = pyo.Constraint(
        model.consultants,
        model.projects,
        rule=lambda mdl, i, j: (
            mdl.hours[i, j] <= mdl.assignment_limits[i, j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[i, j] * model.hours[i, j]
            for i in model.consultants
            for j in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}