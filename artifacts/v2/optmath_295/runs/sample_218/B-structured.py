# IR: {"sets":{"I":[0,1,2,3,4,5,6],"J":[0,1,2,3,4,5]},"params":{"consultant_availability":"real[I], read from params","project_requirement":"real[J], read from params","assignment_cost":"real[I,J], read from params","assignment_limit":"real[I,J], read from params; no placeholder defaults"},"variables":{"hours[i,j]":"continuous, nonnegative"},"constraints":["sum(hours[i,j] for j in J) <= consultant_availability[i] for each i in I","sum(hours[i,j] for i in I) == project_requirement[j] for each j in J","hours[i,j] <= assignment_limit[i,j] for each (i,j) in I x J"],"objective":"minimize sum(assignment_cost[i,j] * hours[i,j] for (i,j) in I x J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.consultants = pyo.RangeSet(0, 6)
    model.projects = pyo.RangeSet(0, 5)

    model.consultant_availability = pyo.Param(
        model.consultants,
        initialize=lambda mdl, i: params["consultant_availability"][i],
        within=pyo.Reals,
    )
    model.project_requirement = pyo.Param(
        model.projects,
        initialize=lambda mdl, j: params["project_requirement"][j],
        within=pyo.Reals,
    )
    model.assignment_cost = pyo.Param(
        model.consultants,
        model.projects,
        initialize=lambda mdl, i, j: params["assignment_cost"][i][j],
        within=pyo.Reals,
    )
    model.assignment_limit = pyo.Param(
        model.consultants,
        model.projects,
        initialize=lambda mdl, i, j: params["assignment_limit"][i][j],
        within=pyo.Reals,
    )

    model.hours = pyo.Var(
        model.consultants,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    def availability_rule(mdl, i):
        return (
            sum(mdl.hours[i, j] for j in mdl.projects)
            <= mdl.consultant_availability[i]
        )

    model.availability_constraints = pyo.Constraint(
        model.consultants, rule=availability_rule
    )

    def requirement_rule(mdl, j):
        return (
            sum(mdl.hours[i, j] for i in mdl.consultants)
            == mdl.project_requirement[j]
        )

    model.requirement_constraints = pyo.Constraint(
        model.projects, rule=requirement_rule
    )

    def assignment_limit_rule(mdl, i, j):
        return mdl.hours[i, j] <= mdl.assignment_limit[i, j]

    model.assignment_limit_constraints = pyo.Constraint(
        model.consultants,
        model.projects,
        rule=assignment_limit_rule,
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
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Unexpected solver errors are allowed to propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}