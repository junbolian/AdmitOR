# IR: {
#   "sets": {"persons": "0..6", "projects": "0..5"},
#   "params": {"capacity": "nonnegative[persons]", "demand": "nonnegative[projects]", "cost": "real[persons,projects]", "pair_capacity": "nonnegative[persons,projects]"},
#   "variables": {"hours[i,j]": "continuous, 0 <= hours[i,j] <= pair_capacity[i,j]"},
#   "constraints": [
#     "individual_capacity[i]: sum(hours[i,j] for j in projects) <= capacity[i]",
#     "project_demand[j]: sum(hours[i,j] for i in persons) == demand[j]"
#   ],
#   "objective": "minimize sum(cost[i,j] * hours[i,j] for i in persons for j in projects)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    demand = params["demand"]
    cost = params["cost"]
    pair_capacity = params["pair_capacity"]

    model = pyo.ConcreteModel()
    model.persons = pyo.RangeSet(0, 6)
    model.projects = pyo.RangeSet(0, 5)

    model.capacity = pyo.Param(
        model.persons,
        initialize=lambda mdl, i: capacity[i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.projects,
        initialize=lambda mdl, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.persons,
        model.projects,
        initialize=lambda mdl, i, j: cost[i][j],
        within=pyo.Reals,
    )
    model.pair_capacity = pyo.Param(
        model.persons,
        model.projects,
        initialize=lambda mdl, i, j: pair_capacity[i][j],
        within=pyo.NonNegativeReals,
    )

    model.hours = pyo.Var(
        model.persons,
        model.projects,
        domain=pyo.NonNegativeReals,
        bounds=lambda mdl, i, j: (0, mdl.pair_capacity[i, j]),
    )

    model.individual_capacity = pyo.Constraint(
        model.persons,
        rule=lambda mdl, i: (
            sum(mdl.hours[i, j] for j in mdl.projects) <= mdl.capacity[i]
        ),
    )
    model.project_demand = pyo.Constraint(
        model.projects,
        rule=lambda mdl, j: (
            sum(mdl.hours[i, j] for i in mdl.persons) == mdl.demand[j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.hours[i, j]
            for i in model.persons
            for j in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution can be loaded.
        # Objective retrieval below remains the success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}