# IR: {"sets":{"C":"range(params['num_centers'])","A":"{(i,j) in C x C: i != j}"},"params":{"num_centers":"number of centers","supply":"supply[i] for i in C","demand":"demand[i] for i in C","transfer_cost":"transfer_cost[i][j] for (i,j) in A"},"variables":{"transfer[i,j]":"nonnegative continuous, (i,j) in A"},"constraints":["For each i in C: supply[i] + sum(transfer[j,i] for j != i) - sum(transfer[i,j] for j != i) >= demand[i]"],"objective":"Minimize sum(transfer_cost[i,j] * transfer[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_centers = params["num_centers"]
    supply = params["supply"]
    demand = params["demand"]
    transfer_cost = params["transfer_cost"]

    model = pyo.ConcreteModel()

    model.centers = pyo.Set(
        initialize=range(num_centers),
        ordered=True,
    )
    model.routes = pyo.Set(
        dimen=2,
        initialize=(
            (i, j)
            for i in range(num_centers)
            for j in range(num_centers)
            if i != j
        ),
    )

    model.initial_supply = pyo.Param(
        model.centers,
        initialize=lambda mdl, i: supply[i],
    )
    model.required_demand = pyo.Param(
        model.centers,
        initialize=lambda mdl, i: demand[i],
    )
    model.unit_cost = pyo.Param(
        model.routes,
        initialize=lambda mdl, i, j: transfer_cost[i][j],
    )

    model.transfer = pyo.Var(
        model.routes,
        domain=pyo.NonNegativeReals,
    )

    def supply_balance_rule(mdl, i):
        incoming = sum(
            mdl.transfer[j, i] for j in mdl.centers if j != i
        )
        outgoing = sum(
            mdl.transfer[i, j] for j in mdl.centers if j != i
        )
        return (
            mdl.initial_supply[i] + incoming - outgoing
            >= mdl.required_demand[i]
        )

    model.supply_balance = pyo.Constraint(
        model.centers,
        rule=supply_balance_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[i, j] * model.transfer[i, j]
            for i, j in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}