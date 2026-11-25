# {
#   "sets": {"I": "0..13", "J": "0..11"},
#   "params": {"supply[i]": "params['supply'][i]", "demand[j]": "params['demand'][j]", "cost[i,j]": "params['cost'][i][j]"},
#   "variables": {"x[i,j]": "nonnegative continuous, i in I, j in J"},
#   "constraints": [
#     "sum(x[i,j] for j in J) <= supply[i], for each i in I",
#     "sum(x[i,j] for i in I) == demand[j], for each j in J"
#   ],
#   "objective": "minimize sum(cost[i,j] * x[i,j] for i in I for j in J)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, 13)
    model.destinations = pyo.RangeSet(0, 11)

    model.supply = pyo.Param(
        model.origins,
        initialize=lambda model, i: params["supply"][i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize=lambda model, j: params["demand"][j],
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda model, i, j: params["cost"][i][j],
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

    # APPsi HiGHS can raise RuntimeError when no solution can be loaded.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    # Success depends solely on whether the objective is retrievable.
    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}