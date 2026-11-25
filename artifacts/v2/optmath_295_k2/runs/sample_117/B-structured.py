# IR: {"sets":{"I":"0..6","J":"0..6"},"params":{"availability":"nonnegative vector[I]","demand":"nonnegative vector[J]","cost":"real matrix[I,J]","pair_cap":"nonnegative matrix[I,J]"},"variables":{"hours[I,J]":"nonnegative continuous"},"constraints":["sum(hours[i,j] for j in J) <= availability[i] for i in I","sum(hours[i,j] for i in I) >= demand[j] for j in J","hours[i,j] <= pair_cap[i,j] for (i,j) in I x J"],"objective":"minimize sum(cost[i,j]*hours[i,j] for (i,j) in I x J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Allocate hours using length-seven vectors and nested 7-by-7 matrices."""
    model = pyo.ConcreteModel()

    model.people = pyo.RangeSet(0, 6)
    model.projects = pyo.RangeSet(0, 6)

    model.availability = pyo.Param(
        model.people,
        initialize=lambda mdl, i: params["availability"][i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.projects,
        initialize=lambda mdl, j: params["demand"][j],
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.people,
        model.projects,
        initialize=lambda mdl, i, j: params["cost"][i][j],
        within=pyo.Reals,
    )
    model.pair_cap = pyo.Param(
        model.people,
        model.projects,
        initialize=lambda mdl, i, j: params["pair_cap"][i][j],
        within=pyo.NonNegativeReals,
    )

    model.hours = pyo.Var(
        model.people,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    model.availability_limits = pyo.Constraint(
        model.people,
        rule=lambda mdl, i: (
            sum(mdl.hours[i, j] for j in mdl.projects)
            <= mdl.availability[i]
        ),
    )
    model.project_requirements = pyo.Constraint(
        model.projects,
        rule=lambda mdl, j: (
            sum(mdl.hours[i, j] for i in mdl.people)
            >= mdl.demand[j]
        ),
    )
    model.pair_limits = pyo.Constraint(
        model.people,
        model.projects,
        rule=lambda mdl, i, j: mdl.hours[i, j] <= mdl.pair_cap[i, j],
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.hours[i, j]
            for i in model.people
            for j in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when automatic solution loading has no solution.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}