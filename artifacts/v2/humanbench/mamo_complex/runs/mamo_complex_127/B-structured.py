# IR: {"sets":{"F":"{0,...,6}","A":"{(i,j) in F x F: i != j}"},"params":{"initial_supply":"nonnegative vector indexed by F; required input","required_supply":"nonnegative vector indexed by F; required input","transfer_cost":"nonnegative 7-by-7 matrix; diagonal unused; required input"},"variables":{"transfer[i,j]":"nonnegative real for (i,j) in A"},"constraints":["For each i in F: initial_supply[i] + sum(transfer[j,i] for j in F if j != i) - sum(transfer[i,j] for j in F if j != i) = required_supply[i]"],"objective":"minimize sum(transfer_cost[i,j] * transfer[i,j] for (i,j) in A)","input_validation":"If a required parameter is missing, return objective=null and status=missing_<parameter>; do not invent defaults","success":"Return optimal only when the solved objective is retrievable"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # A missing cost matrix cannot be reconstructed without inventing input.
    for parameter_name in (
        "initial_supply",
        "required_supply",
        "transfer_cost",
    ):
        if parameter_name not in params:
            return {
                "objective": None,
                "status": f"missing_{parameter_name}",
            }

    initial_supply = params["initial_supply"]
    required_supply = params["required_supply"]
    transfer_cost = params["transfer_cost"]

    model = pyo.ConcreteModel()
    model.facilities = pyo.RangeSet(0, 6)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.facilities
            for j in model.facilities
            if i != j
        ],
    )

    model.initial_supply = pyo.Param(
        model.facilities,
        initialize={i: initial_supply[i] for i in model.facilities},
        within=pyo.NonNegativeReals,
    )
    model.required_supply = pyo.Param(
        model.facilities,
        initialize={i: required_supply[i] for i in model.facilities},
        within=pyo.NonNegativeReals,
    )
    model.transfer_cost = pyo.Param(
        model.arcs,
        initialize={(i, j): transfer_cost[i][j] for i, j in model.arcs},
        within=pyo.NonNegativeReals,
    )

    model.transfer = pyo.Var(
        model.arcs,
        domain=pyo.NonNegativeReals,
    )

    def supply_balance_rule(block, i):
        incoming = sum(
            block.transfer[j, i]
            for j in block.facilities
            if j != i
        )
        outgoing = sum(
            block.transfer[i, j]
            for j in block.facilities
            if j != i
        )
        return (
            block.initial_supply[i] + incoming - outgoing
            == block.required_supply[i]
        )

    model.supply_balance = pyo.Constraint(
        model.facilities,
        rule=supply_balance_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.transfer_cost[i, j] * model.transfer[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    # Exact balances conserve total supply; surplus disposal is not allowed.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}