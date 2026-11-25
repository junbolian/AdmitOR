# IR: {"sets":{"I":"0..5","J":"0..5"},"params":{"supply":"params['supply'][i], i in I","demand":"params['demand'][j], j in J","cost":"params['cost'][i][j], (i,j) in I x J"},"variables":{"shipment[i,j]":"NonNegativeReals, (i,j) in I x J"},"constraints":["sum(shipment[i,j] for j in J) == supply[i], for each i in I","sum(shipment[i,j] for i in I) == demand[j], for each j in J"],"objective":"minimize sum(cost[i,j] * shipment[i,j] for (i,j) in I x J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, 5)
    model.J = pyo.RangeSet(0, 5)

    model.supply = pyo.Param(
        model.I,
        initialize={i: supply[i] for i in model.I},
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.J,
        initialize={j: demand[j] for j in model.J},
        within=pyo.Reals,
    )
    model.cost = pyo.Param(
        model.I,
        model.J,
        initialize={
            (i, j): cost[i][j]
            for i in model.I
            for j in model.J
        },
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.I,
        model.J,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(instance, i):
        return (
            sum(instance.shipment[i, j] for j in instance.J)
            == instance.supply[i]
        )

    def demand_rule(instance, j):
        return (
            sum(instance.shipment[i, j] for i in instance.I)
            == instance.demand[j]
        )

    model.supply_balance = pyo.Constraint(model.I, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.J, rule=demand_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.shipment[i, j]
            for i in model.I
            for j in model.J
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