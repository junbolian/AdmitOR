# IR: {"sets":{"I":"0..5","J":"0..5"},"params":{"supply":"nonnegative real[I], params['supply'][i]","demand":"nonnegative real[J], params['demand'][j]","cost":"real[I,J], params['cost'][i][j]","capacity":"nonnegative real[I,J], params['capacity'][i][j]"},"variables":{"shipment[i,j]":"nonnegative continuous, i in I, j in J"},"constraints":["sum(j in J, shipment[i,j]) == supply[i] for each i in I","sum(i in I, shipment[i,j]) == demand[j] for each j in J","shipment[i,j] <= capacity[i,j] for each (i,j) in I x J"],"objective":"minimize sum(i in I, j in J, cost[i,j] * shipment[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 5)
    model.J = pyo.RangeSet(0, 5)

    model.supply = pyo.Param(
        model.I,
        initialize={i: params["supply"][i] for i in model.I},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.J,
        initialize={j: params["demand"][j] for j in model.J},
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.I,
        model.J,
        initialize={
            (i, j): params["cost"][i][j]
            for i in model.I
            for j in model.J
        },
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.I,
        model.J,
        initialize={
            (i, j): params["capacity"][i][j]
            for i in model.I
            for j in model.J
        },
        within=pyo.NonNegativeReals,
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

    def capacity_rule(instance, i, j):
        return instance.shipment[i, j] <= instance.capacity[i, j]

    model.supply_balance = pyo.Constraint(model.I, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.J, rule=demand_rule)
    model.arc_capacity = pyo.Constraint(
        model.I, model.J, rule=capacity_rule
    )

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
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, RuntimeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}