# IR: {"sets":{"W":[0,1,2,3],"A":"{(i,j) in W x W: i != j}"},"params":{"initial_stock":"W -> nonnegative real, from params","required_demand":"W -> nonnegative real, from params","transport_cost":"W x W -> real, from params"},"variables":{"shipment":"A -> nonnegative continuous tons"},"constraints":["For each i in W: initial_stock[i] + sum(shipment[j,i] for j != i) - sum(shipment[i,j] for j != i) >= required_demand[i]"],"objective":"Minimize sum(transport_cost[i,j] * shipment[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.W = pyo.RangeSet(0, 3)
    model.A = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.W
            for j in model.W
            if i != j
        ],
    )

    model.initial_stock = pyo.Param(
        model.W,
        initialize=lambda instance, i: params["initial_stock"][i],
        within=pyo.NonNegativeReals,
    )
    model.required_demand = pyo.Param(
        model.W,
        initialize=lambda instance, i: params["required_demand"][i],
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.W,
        model.W,
        initialize=lambda instance, i, j: params["transport_cost"][i][j],
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.A,
        domain=pyo.NonNegativeReals,
    )

    def stock_requirement(instance, i):
        inbound = sum(
            instance.shipment[j, i]
            for j in instance.W
            if j != i
        )
        outbound = sum(
            instance.shipment[i, j]
            for j in instance.W
            if j != i
        )
        return (
            instance.initial_stock[i] + inbound - outbound
            >= instance.required_demand[i]
        )

    model.stock_requirement = pyo.Constraint(
        model.W,
        rule=stock_requirement,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[i, j] * model.shipment[i, j]
            for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution can be loaded.
        # Objective retrieval below is the sole success test.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}