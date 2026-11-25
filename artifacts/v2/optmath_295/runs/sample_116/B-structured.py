# IR: {"sets":{"I":"0..7","J":"0..7"},"params":{"consultant_availability":"A[i]","project_requirements":"R[j]","assignment_costs":"C[i,j]","assignment_capacity":"U[i,j]"},"variables":{"x[i,j]":"continuous nonnegative hours"},"constraints":["sum(x[i,j] for j in J) == A[i] for i in I","sum(x[i,j] for i in I) == R[j] for j in J","x[i,j] <= U[i,j] for (i,j) in I x J"],"objective":"minimize sum(C[i,j]*x[i,j] for (i,j) in I x J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["consultant_availability"]
    requirements = params["project_requirements"]
    costs = params["assignment_costs"]
    capacity = params["assignment_capacity"]

    model = pyo.ConcreteModel()
    model.consultants = pyo.RangeSet(0, 7)
    model.projects = pyo.RangeSet(0, 7)

    model.available_hours = pyo.Param(
        model.consultants,
        initialize=lambda mdl, i: availability[i],
        within=pyo.NonNegativeReals,
    )
    model.required_hours = pyo.Param(
        model.projects,
        initialize=lambda mdl, j: requirements[j],
        within=pyo.NonNegativeReals,
    )
    model.hourly_cost = pyo.Param(
        model.consultants,
        model.projects,
        initialize=lambda mdl, i, j: costs[i][j],
        within=pyo.Reals,
    )
    model.pair_capacity = pyo.Param(
        model.consultants,
        model.projects,
        initialize=lambda mdl, i, j: capacity[i][j],
        within=pyo.NonNegativeReals,
    )

    model.assigned_hours = pyo.Var(
        model.consultants,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    model.supply_constraints = pyo.Constraint(
        model.consultants,
        rule=lambda mdl, i: sum(
            mdl.assigned_hours[i, j] for j in mdl.projects
        ) == mdl.available_hours[i],
    )
    model.demand_constraints = pyo.Constraint(
        model.projects,
        rule=lambda mdl, j: sum(
            mdl.assigned_hours[i, j] for i in mdl.consultants
        ) == mdl.required_hours[j],
    )
    model.capacity_constraints = pyo.Constraint(
        model.consultants,
        model.projects,
        rule=lambda mdl, i, j: (
            mdl.assigned_hours[i, j] <= mdl.pair_capacity[i, j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.hourly_cost[i, j] * model.assigned_hours[i, j]
            for i in model.consultants
            for j in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # A failed solve can leave the objective without a numeric value.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}