# IR: {"sets":{"R":[1,2,3,4,5,6],"A":"{(i,j) in R x R: i != j}"},"params":{"supply":"R-indexed nonnegative stock from params['supply']","demand":"R-indexed nonnegative requirement from params['demand']","cost":"A-indexed transport cost from params['cost_i_j']"},"variables":{"flow[i,j]":"continuous nonnegative, (i,j) in A"},"constraints":["For each i in R: supply[i] + sum(flow[j,i] for j != i) - sum(flow[i,j] for j != i) >= demand[i]"],"objective":"Minimize sum(cost[i,j] * flow[i,j] for (i,j) in A)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept regional data as six-element sequences or mappings keyed 1..6."""

    regions = range(1, 7)

    def regional_values(data):
        if isinstance(data, Mapping):
            return {
                region: data[region] if region in data else data[str(region)]
                for region in regions
            }
        if len(data) != len(regions):
            raise ValueError("Regional sequences must contain exactly six values.")
        return {region: data[region - 1] for region in regions}

    supply_values = regional_values(params["supply"])
    demand_values = regional_values(params["demand"])
    transport_costs = {
        (origin, destination): params[f"cost_{origin}_{destination}"]
        for origin in regions
        for destination in regions
        if origin != destination
    }

    model = pyo.ConcreteModel()
    model.regions = pyo.Set(initialize=regions, ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=transport_costs.keys(),
        ordered=True,
    )

    model.stock = pyo.Param(
        model.regions,
        initialize=supply_values,
        within=pyo.NonNegativeReals,
    )
    model.requirement = pyo.Param(
        model.regions,
        initialize=demand_values,
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.arcs,
        initialize=transport_costs,
        within=pyo.Reals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def food_balance_rule(instance, region):
        incoming = sum(
            instance.flow[other, region]
            for other in instance.regions
            if other != region
        )
        outgoing = sum(
            instance.flow[region, other]
            for other in instance.regions
            if other != region
        )
        return (
            instance.stock[region] + incoming - outgoing
            >= instance.requirement[region]
        )

    model.food_balance = pyo.Constraint(
        model.regions,
        rule=food_balance_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[origin, destination]
            * model.flow[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPSI raises this when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}