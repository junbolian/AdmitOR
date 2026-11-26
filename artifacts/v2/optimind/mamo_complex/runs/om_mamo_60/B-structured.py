# {
#   "sets": {"R": [1, 2, 3, 4, 5, 6], "A": "ordered pairs (i,j) in R x R with i != j"},
#   "params": {"stock[i]": "params['stock'], nonnegative", "demand[i]": "params['demand'], nonnegative", "cost[i,j]": "params[f'cost_{i}_{j}']"},
#   "variables": {"ship[i,j]": "continuous nonnegative, (i,j) in A", "local[i]": "continuous nonnegative, i in R"},
#   "constraints": [
#     "supply[i]: local[i] + sum(ship[i,j] for j != i) <= stock[i]",
#     "requirements[i]: local[i] + sum(ship[j,i] for j != i) == demand[i]"
#   ],
#   "objective": "minimize sum(cost[i,j] * ship[i,j] for (i,j) in A)",
#   "interpretation": "Stocks are supply capacities; surplus may remain unused. Each region receives exactly its demand."
# }

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Minimize transportation cost while meeting every region's demand exactly.

    params["stock"] and params["demand"] must each be either:
      - a mapping keyed by region integers 1 through 6; or
      - a six-element sequence ordered by region 1 through region 6.

    All thirty off-diagonal transportation costs are read from params.
    Surplus stock may remain unused at its original region.
    """
    regions = tuple(range(1, 7))
    arcs = tuple(
        (origin, destination)
        for origin in regions
        for destination in regions
        if origin != destination
    )

    stock_input = params["stock"]
    demand_input = params["demand"]

    def regional_values(values):
        if isinstance(values, Mapping):
            return {region: values[region] for region in regions}
        if len(values) != len(regions):
            raise ValueError("Regional sequences must contain exactly six values.")
        return {region: values[region - 1] for region in regions}

    stock_values = regional_values(stock_input)
    demand_values = regional_values(demand_input)
    cost_values = {
        (origin, destination): params[f"cost_{origin}_{destination}"]
        for origin, destination in arcs
    }

    model = pyo.ConcreteModel()

    model.regions = pyo.Set(initialize=regions, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.stock = pyo.Param(
        model.regions,
        initialize=stock_values,
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.regions,
        initialize=demand_values,
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.arcs,
        initialize=cost_values,
        within=pyo.Reals,
    )

    model.ship = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.local = pyo.Var(model.regions, domain=pyo.NonNegativeReals)

    def supply_rule(instance, region):
        return (
            instance.local[region]
            + sum(
                instance.ship[region, destination]
                for destination in instance.regions
                if destination != region
            )
            <= instance.stock[region]
        )

    def requirements_rule(instance, region):
        return (
            instance.local[region]
            + sum(
                instance.ship[origin, region]
                for origin in instance.regions
                if origin != region
            )
            == instance.demand[region]
        )

    model.supply_limits = pyo.Constraint(model.regions, rule=supply_rule)
    model.demand_requirements = pyo.Constraint(
        model.regions, rule=requirements_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[origin, destination]
            * model.ship[origin, destination]
            for origin, destination in model.arcs
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