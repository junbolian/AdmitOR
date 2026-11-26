# IR: {"sets":{"R":[1,2,3,4,5,6],"A":"{(i,j): i,j in R, i != j}"},"params":{"supply":"params['supply'], indexed by region","demand":"params['demand'], indexed by region","cost[i,j]":"params[f'cost_{i}_to_{j}']"},"variables":{"flow[i,j]":"nonnegative continuous, (i,j) in A","unused[i]":"nonnegative continuous, i in R"},"constraints":["unused[i] <= supply[i] for each i in R","supply[i] - unused[i] + sum(flow[j,i] for j != i) - sum(flow[i,j] for j != i) == demand[i] for each i in R"],"objective":"minimize sum(cost[i,j] * flow[i,j] for (i,j) in A)","assumption":"Surplus stock may be set aside as unused; each region's active stock equals its demand exactly."}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _region_values(data):
    """Accept a six-element sequence or a mapping keyed by region 1 through 6."""
    if isinstance(data, Mapping):
        return {
            region: data[region] if region in data else data[str(region)]
            for region in range(1, 7)
        }

    if len(data) != 6:
        raise ValueError("Supply and demand sequences must contain six values.")

    return {region: data[region - 1] for region in range(1, 7)}


def solve(params):
    supply_values = _region_values(params["supply"])
    demand_values = _region_values(params["demand"])
    arcs = [
        (origin, destination)
        for origin in range(1, 7)
        for destination in range(1, 7)
        if origin != destination
    ]
    cost_values = {
        (origin, destination): params[f"cost_{origin}_to_{destination}"]
        for origin, destination in arcs
    }

    model = pyo.ConcreteModel()
    model.regions = pyo.RangeSet(1, 6)
    model.arcs = pyo.Set(dimen=2, initialize=arcs)

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
        initialize=cost_values,
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.unused = pyo.Var(model.regions, domain=pyo.NonNegativeReals)

    def unused_limit_rule(instance, region):
        return instance.unused[region] <= instance.stock[region]

    model.unused_limit = pyo.Constraint(
        model.regions, rule=unused_limit_rule
    )

    def balance_rule(instance, region):
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
            instance.stock[region]
            - instance.unused[region]
            + incoming
            - outgoing
            == instance.requirement[region]
        )

    model.resource_balance = pyo.Constraint(
        model.regions, rule=balance_rule
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
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}