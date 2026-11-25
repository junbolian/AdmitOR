# IR: {
#   "sets": {"I": "0..6", "J": "0..5"},
#   "params": {
#     "capacity_person[i]": "params['capacity_person'][i]",
#     "demand_project[j]": "params['demand_project'][j]",
#     "cost_assign[i,j]": "params['cost_assign'][i][j]",
#     "max_person_project[i,j]": "params['max_person_project'][i][j]"
#   },
#   "variables": {"hours[i,j]": "nonnegative continuous"},
#   "constraints": [
#     "sum(hours[i,j] for j in J) <= capacity_person[i] for each i in I",
#     "sum(hours[i,j] for i in I) == demand_project[j] for each j in J",
#     "hours[i,j] <= max_person_project[i,j] for each (i,j) in I x J"
#   ],
#   "objective": "minimize sum(cost_assign[i,j] * hours[i,j] for (i,j) in I x J)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the allocation LP using indexed vectors and nested cost/limit arrays."""
    capacity_person = params["capacity_person"]
    demand_project = params["demand_project"]
    cost_assign = params["cost_assign"]
    max_person_project = params["max_person_project"]

    model = pyo.ConcreteModel()
    model.people = pyo.RangeSet(0, 6)
    model.projects = pyo.RangeSet(0, 5)

    model.person_capacity = pyo.Param(
        model.people,
        initialize=lambda mdl, i: capacity_person[i],
    )
    model.project_demand = pyo.Param(
        model.projects,
        initialize=lambda mdl, j: demand_project[j],
    )
    model.assignment_cost = pyo.Param(
        model.people,
        model.projects,
        initialize=lambda mdl, i, j: cost_assign[i][j],
    )
    model.assignment_limit = pyo.Param(
        model.people,
        model.projects,
        initialize=lambda mdl, i, j: max_person_project[i][j],
    )

    model.hours = pyo.Var(
        model.people,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    model.capacity_constraints = pyo.Constraint(
        model.people,
        rule=lambda mdl, i: (
            sum(mdl.hours[i, j] for j in mdl.projects)
            <= mdl.person_capacity[i]
        ),
    )
    model.demand_constraints = pyo.Constraint(
        model.projects,
        rule=lambda mdl, j: (
            sum(mdl.hours[i, j] for i in mdl.people)
            == mdl.project_demand[j]
        ),
    )
    model.assignment_constraints = pyo.Constraint(
        model.people,
        model.projects,
        rule=lambda mdl, i, j: (
            mdl.hours[i, j] <= mdl.assignment_limit[i, j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[i, j] * model.hours[i, j]
            for i in model.people
            for j in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}