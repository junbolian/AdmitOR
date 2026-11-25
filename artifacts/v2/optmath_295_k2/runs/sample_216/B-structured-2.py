# IR: {"sets":{"I":"0..6","J":"0..7"},"params":{"supply":"params['supply'][i]","demand":"params['demand'][j]","cost":"params['cost'][i][j]"},"variables":{"shipment[i,j]":"nonnegative continuous"},"constraints":["sum(shipment[i,j] for j in J) == supply[i] for each i in I","sum(shipment[i,j] for i in I) == demand[j] for each j in J"],"objective":"minimize sum(cost[i,j] * shipment[i,j] for i in I for j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using supply[7], demand[8], and cost[7][8] input arrays."""
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.warehouses = pyo.RangeSet(0, 6)
    model.stores = pyo.RangeSet(0, 7)

    model.stock = pyo.Param(
        model.warehouses,
        initialize=lambda model, i: supply[i],
        within=pyo.NonNegativeReals,
    )
    model.requirement = pyo.Param(
        model.stores,
        initialize=lambda model, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.warehouses,
        model.stores,
        initialize=lambda model, i, j: cost[i][j],
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.warehouses,
        model.stores,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(model, i):
        return (
            sum(model.shipment[i, j] for j in model.stores)
            == model.stock[i]
        )

    def demand_rule(model, j):
        return (
            sum(model.shipment[i, j] for i in model.warehouses)
            == model.requirement[j]
        )

    model.supply_balance = pyo.Constraint(
        model.warehouses, rule=supply_rule
    )
    model.demand_balance = pyo.Constraint(
        model.stores, rule=demand_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[i, j] * model.shipment[i, j]
            for i in model.warehouses
            for j in model.stores
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}