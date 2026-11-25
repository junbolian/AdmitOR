# IR: {
#   "sets": {"I": "0..13", "J": "0..11"},
#   "params": {"supply": "supply[I]", "demand": "demand[J]", "cost": "cost[I][J]"},
#   "variables": {"x[I,J]": "nonnegative continuous"},
#   "constraints": [
#     "sum(x[i,j] for j in J) <= supply[i] for each i in I",
#     "sum(x[i,j] for i in I) == demand[j] for each j in J"
#   ],
#   "objective": "minimize sum(cost[i][j] * x[i,j] for i in I for j in J)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 13)
    model.destinations = pyo.RangeSet(0, 11)

    model.supply = pyo.Param(
        model.origins,
        initialize={i: supply[i] for i in model.origins},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize={j: demand[j] for j in model.destinations},
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (i, j): cost[i][j]
            for i in model.origins
            for j in model.destinations
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(model, i):
        return (
            sum(model.x[i, j] for j in model.destinations)
            <= model.supply[i]
        )

    def demand_rule(model, j):
        return (
            sum(model.x[i, j] for i in model.origins)
            == model.demand[j]
        )

    model.supply_limits = pyo.Constraint(
        model.origins, rule=supply_rule
    )
    model.demand_requirements = pyo.Constraint(
        model.destinations, rule=demand_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.x[i, j]
            for i in model.origins
            for j in model.destinations
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