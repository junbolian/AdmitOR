# IR: {"sets":{"warehouses":"0..11","stores":"0..13"},"params":{"supply":"params['supply'][i]","demand":"params['demand'][j]","transport_cost":"params['transport_cost'][i][j]"},"variables":{"shipment[i,j]":"continuous, nonnegative"},"constraints":["sum_j shipment[i,j] == supply[i] for each warehouse i","sum_i shipment[i,j] == demand[j] for each store j"],"objective":"minimize sum_i sum_j transport_cost[i,j] * shipment[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    model = pyo.ConcreteModel()

    model.warehouses = pyo.RangeSet(0, 11)
    model.stores = pyo.RangeSet(0, 13)

    model.supply = pyo.Param(
        model.warehouses,
        initialize={i: supply[i] for i in model.warehouses},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.stores,
        initialize={j: demand[j] for j in model.stores},
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.warehouses,
        model.stores,
        initialize={
            (i, j): transport_cost[i][j]
            for i in model.warehouses
            for j in model.stores
        },
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.warehouses,
        model.stores,
        domain=pyo.NonNegativeReals,
    )

    def supply_balance_rule(instance, i):
        return (
            sum(instance.shipment[i, j] for j in instance.stores)
            == instance.supply[i]
        )

    def demand_balance_rule(instance, j):
        return (
            sum(instance.shipment[i, j] for i in instance.warehouses)
            == instance.demand[j]
        )

    model.supply_balance = pyo.Constraint(
        model.warehouses, rule=supply_balance_rule
    )
    model.demand_balance = pyo.Constraint(
        model.stores, rule=demand_balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[i, j] * model.shipment[i, j]
            for i in model.warehouses
            for j in model.stores
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