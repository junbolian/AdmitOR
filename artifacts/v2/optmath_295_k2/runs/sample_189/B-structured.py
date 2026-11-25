# IR: {"sets":{"I":[0,1,2,3],"J":[0,1,2,3,4]},"params":{"consultant_availability":"nonnegative[I]","project_requirements":"nonnegative[J]","cost_matrix":"real[I,J]","assignment_capacity":"nonnegative[I,J]"},"variables":{"hours[i,j]":"continuous nonnegative"},"constraints":["sum(j in J, hours[i,j]) <= consultant_availability[i] for i in I","sum(i in I, hours[i,j]) >= project_requirements[j] for j in J","hours[i,j] <= assignment_capacity[i,j] for i in I, j in J"],"objective":"minimize sum(i in I, j in J, cost_matrix[i,j] * hours[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.consultants = pyo.RangeSet(0, 3)
    model.projects = pyo.RangeSet(0, 4)

    model.consultant_availability = pyo.Param(
        model.consultants,
        initialize=lambda mdl, i: params["consultant_availability"][i],
        within=pyo.NonNegativeReals,
    )
    model.project_requirements = pyo.Param(
        model.projects,
        initialize=lambda mdl, j: params["project_requirements"][j],
        within=pyo.NonNegativeReals,
    )
    model.cost_matrix = pyo.Param(
        model.consultants,
        model.projects,
        initialize=lambda mdl, i, j: params["cost_matrix"][i][j],
        within=pyo.Reals,
    )
    model.assignment_capacity = pyo.Param(
        model.consultants,
        model.projects,
        initialize=lambda mdl, i, j: params["assignment_capacity"][i][j],
        within=pyo.NonNegativeReals,
    )

    model.hours = pyo.Var(
        model.consultants,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    model.availability_limits = pyo.Constraint(
        model.consultants,
        rule=lambda mdl, i: sum(
            mdl.hours[i, j] for j in mdl.projects
        ) <= mdl.consultant_availability[i],
    )
    model.project_coverage = pyo.Constraint(
        model.projects,
        rule=lambda mdl, j: sum(
            mdl.hours[i, j] for i in mdl.consultants
        ) >= mdl.project_requirements[j],
    )
    model.assignment_limits = pyo.Constraint(
        model.consultants,
        model.projects,
        rule=lambda mdl, i, j: (
            mdl.hours[i, j] <= mdl.assignment_capacity[i, j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost_matrix[i, j] * model.hours[i, j]
            for i in model.consultants
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
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}