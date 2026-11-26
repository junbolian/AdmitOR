# IR: {"sets":{"H":"0..6","A":"{(i,j) in H x H: i != j}"},"params":{"stock":"nonnegative vector indexed by H, from params['stock']","demand":"nonnegative vector indexed by H, from params['demand']","transfer_cost":"nonnegative matrix indexed by H x H, from params['transfer_cost']"},"variables":{"transfer[i,j]":"nonnegative continuous, (i,j) in A"},"constraints":["stock[h] + sum(transfer[i,h] for i != h) - sum(transfer[h,j] for j != h) >= demand[h], for each h in H"],"objective":"minimize sum(transfer_cost[i,j] * transfer[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using length-seven vectors and a 7-by-7 cost matrix.

    Input sequences use zero-based hospital indices. Transfers may pass
    through intermediate hospitals, provided every final stock meets demand.
    """
    stock = params["stock"]
    demand = params["demand"]
    transfer_cost = params["transfer_cost"]

    model = pyo.ConcreteModel()

    model.hospitals = pyo.RangeSet(0, 6)
    model.routes = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.hospitals
            for j in model.hospitals
            if i != j
        ],
    )

    model.initial_stock = pyo.Param(
        model.hospitals,
        initialize={i: stock[i] for i in model.hospitals},
        within=pyo.NonNegativeReals,
    )
    model.required_supply = pyo.Param(
        model.hospitals,
        initialize={i: demand[i] for i in model.hospitals},
        within=pyo.NonNegativeReals,
    )
    model.route_cost = pyo.Param(
        model.hospitals,
        model.hospitals,
        initialize={
            (i, j): transfer_cost[i][j]
            for i in model.hospitals
            for j in model.hospitals
        },
        within=pyo.NonNegativeReals,
    )

    model.transfer = pyo.Var(
        model.routes,
        domain=pyo.NonNegativeReals,
    )

    def supply_balance_rule(instance, h):
        incoming = sum(
            instance.transfer[i, h]
            for i in instance.hospitals
            if i != h
        )
        outgoing = sum(
            instance.transfer[h, j]
            for j in instance.hospitals
            if j != h
        )
        return (
            instance.initial_stock[h] + incoming - outgoing
            >= instance.required_supply[h]
        )

    model.supply_balance = pyo.Constraint(
        model.hospitals,
        rule=supply_balance_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[i, j] * model.transfer[i, j]
            for i, j in model.routes
        ),
        sense=pyo.minimize,
    )

    # Appsi can raise RuntimeError when no feasible solution can be loaded.
    # Success is determined exclusively by retrieving the objective below.
    solve_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solve_failed = True

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, RuntimeError):
        return {
            "objective": None,
            "status": "solve_failed" if solve_failed else "no_objective",
        }

    return {"objective": obj_val, "status": "optimal"}