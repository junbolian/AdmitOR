# IR: {"sets":{"R":"{0,1,2,3,4}","A":"{(i,j) in R x R: i != j}"},"params":{"supplies":"params['supplies'][i], i in R","demands":"params['demands'][i], i in R","transfer_costs":"params['transfer_costs'][i][j], (i,j) in A"},"variables":{"transfer[i,j]":"nonnegative continuous, (i,j) in A"},"constraints":["supplies[i] + sum(transfer[j,i] for j != i) - sum(transfer[i,j] for j != i) >= demands[i], for each i in R"],"objective":"minimize sum(transfer_costs[i,j] * transfer[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supplies = params["supplies"]
    demands = params["demands"]
    transfer_costs = params["transfer_costs"]

    model = pyo.ConcreteModel()
    model.regions = pyo.Set(initialize=range(5), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.regions
            for j in model.regions
            if i != j
        ],
    )

    model.stock = pyo.Param(
        model.regions,
        initialize={i: supplies[i] for i in model.regions},
    )
    model.requirement = pyo.Param(
        model.regions,
        initialize={i: demands[i] for i in model.regions},
    )
    model.unit_cost = pyo.Param(
        model.arcs,
        initialize={
            (i, j): transfer_costs[i][j]
            for i, j in model.arcs
        },
    )
    model.transfer = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def supply_balance_rule(instance, i):
        incoming = sum(
            instance.transfer[j, i]
            for j in instance.regions
            if j != i
        )
        outgoing = sum(
            instance.transfer[i, j]
            for j in instance.regions
            if j != i
        )
        return (
            instance.stock[i] + incoming - outgoing
            >= instance.requirement[i]
        )

    model.supply_balance = pyo.Constraint(
        model.regions,
        rule=supply_balance_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[i, j] * model.transfer[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}