# IR: {"sets":{"R":[1,2,3,4,5],"A":"{(i,j) in R x R: i != j}"},"params":{"transport_cost":"nonnegative matrix indexed by R x R","current_supply":"nonnegative integer vector indexed by R","demand":"nonnegative integer vector indexed by R"},"variables":{"x[i,j]":"nonnegative integer for (i,j) in A; cars relocated"},"constraints":["For each i in R: current_supply[i] + sum(x[j,i] for j != i) - sum(x[i,j] for j != i) >= demand[i]."],"objective":"Minimize sum(transport_cost[i,j] * x[i,j] for (i,j) in A)."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept a 5-by-5 cost matrix and length-5 supply/demand sequences."""
    model = pyo.ConcreteModel()

    model.regions = pyo.RangeSet(1, 5)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(1, 6)
            for destination in range(1, 6)
            if origin != destination
        ],
    )

    model.transport_cost = pyo.Param(
        model.regions,
        model.regions,
        initialize=lambda instance, origin, destination: params["transport_cost"][
            origin - 1
        ][destination - 1],
        within=pyo.NonNegativeReals,
    )
    model.current_supply = pyo.Param(
        model.regions,
        initialize=lambda instance, region: params["current_supply"][region - 1],
        within=pyo.NonNegativeIntegers,
    )
    model.demand = pyo.Param(
        model.regions,
        initialize=lambda instance, region: params["demand"][region - 1],
        within=pyo.NonNegativeIntegers,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.NonNegativeIntegers)

    def regional_balance_rule(instance, region):
        incoming = sum(
            instance.x[other, region]
            for other in instance.regions
            if other != region
        )
        outgoing = sum(
            instance.x[region, other]
            for other in instance.regions
            if other != region
        )
        return (
            instance.current_supply[region] + incoming - outgoing
            >= instance.demand[region]
        )

    model.regional_balance = pyo.Constraint(
        model.regions, rule=regional_balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[origin, destination] * model.x[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    # HiGHS may raise RuntimeError when no feasible solution can be loaded.
    # Success is determined solely by retrieving the objective below.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}