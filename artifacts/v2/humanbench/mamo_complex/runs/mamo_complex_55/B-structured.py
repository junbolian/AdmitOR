# IR: {"sets":{"R":[1,2,3,4,5],"A":"{(i,j) in R x R: i != j}"},"params":{"cost[i,j]":"params['cost_i_j'] for (i,j) in A","supply[i]":"params['supply_i'] for i in R","demand[i]":"params['demand_i'] for i in R"},"variables":{"moved[i,j]":{"type":"nonnegative_integer","index":"A"}},"constraints":["supply[i] + sum(moved[j,i] for j != i) - sum(moved[i,j] for j != i) >= demand[i], for each i in R"],"objective":{"sense":"minimize","expression":"sum(cost[i,j] * moved[i,j] for (i,j) in A)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.regions = pyo.Set(initialize=range(1, 6), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.regions
            for j in model.regions
            if i != j
        ],
        ordered=True,
    )

    model.move_cost = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"cost_{i}_{j}"]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )
    model.initial_supply = pyo.Param(
        model.regions,
        initialize={i: params[f"supply_{i}"] for i in model.regions},
        within=pyo.NonNegativeIntegers,
    )
    model.required_cars = pyo.Param(
        model.regions,
        initialize={i: params[f"demand_{i}"] for i in model.regions},
        within=pyo.NonNegativeIntegers,
    )

    model.moved = pyo.Var(model.arcs, domain=pyo.NonNegativeIntegers)

    def regional_balance_rule(mdl, i):
        incoming = sum(
            mdl.moved[j, i] for j in mdl.regions if j != i
        )
        outgoing = sum(
            mdl.moved[i, j] for j in mdl.regions if j != i
        )
        return (
            mdl.initial_supply[i] + incoming - outgoing
            >= mdl.required_cars[i]
        )

    model.regional_balance = pyo.Constraint(
        model.regions, rule=regional_balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.move_cost[i, j] * model.moved[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    # APPsi can raise RuntimeError when no solution can be loaded.
    # Success is determined solely by objective-value retrieval below.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}