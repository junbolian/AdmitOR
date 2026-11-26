# IR: {"sets":{"R":[0,1,2,3,4],"A":"{(i,j) in R x R : i != j}"},"params":{"stock":"params['stock'][i] for i in R","need":"params['need'][i] for i in R","cost":"params['cost'][i][j] for (i,j) in A"},"variables":{"transfer[i,j]":"nonnegative continuous for (i,j) in A"},"constraints":["For each i: stock[i] + sum(transfer[j,i] for j != i) - sum(transfer[i,j] for j != i) >= need[i]"],"objective":"Minimize sum(cost[i,j] * transfer[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Inputs use zero-based region indices; intermediate transfers are allowed."""
    stock = params["stock"]
    need = params["need"]
    cost = params["cost"]

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

    model.initial_stock = pyo.Param(
        model.regions,
        initialize={i: stock[i] for i in model.regions},
    )
    model.required_stock = pyo.Param(
        model.regions,
        initialize={i: need[i] for i in model.regions},
    )
    model.unit_cost = pyo.Param(
        model.arcs,
        initialize={(i, j): cost[i][j] for i, j in model.arcs},
    )

    model.transfer = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def regional_balance_rule(instance, i):
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
            instance.initial_stock[i] + incoming - outgoing
            >= instance.required_stock[i]
        )

    model.regional_balance = pyo.Constraint(
        model.regions,
        rule=regional_balance_rule,
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
    except RuntimeError as error:
        message = str(error).lower()
        if (
            "a feasible solution was not found" in message
            or "no feasible solution can be loaded" in message
        ):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}