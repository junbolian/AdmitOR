# IR: {"sets":{"I":[0,1,2,3],"J":[0,1,2,3,4]},"params":{"supply":"params['supply'][i], nonnegative","demand":"params['demand'][j], nonnegative","cost":"params['cost'][i][j], real","capacity":"params['capacity'][i][j], nonnegative"},"variables":{"shipment[i,j]":"continuous nonnegative"},"constraints":["For each i: sum_j shipment[i,j] = supply[i]","For each j: sum_i shipment[i,j] = demand[j]","For each i,j: shipment[i,j] <= capacity[i,j]"],"objective":"minimize sum_i sum_j cost[i,j] * shipment[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using indexed supply/demand and nested indexed cost/capacity."""
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.warehouses = pyo.RangeSet(0, 3)
    model.stores = pyo.RangeSet(0, 4)

    model.supply = pyo.Param(
        model.warehouses,
        initialize=lambda mdl, i: supply[i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.stores,
        initialize=lambda mdl, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.warehouses,
        model.stores,
        initialize=lambda mdl, i, j: cost[i][j],
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.warehouses,
        model.stores,
        initialize=lambda mdl, i, j: capacity[i][j],
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.warehouses,
        model.stores,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mdl, i):
        return sum(mdl.shipment[i, j] for j in mdl.stores) == mdl.supply[i]

    def demand_rule(mdl, j):
        return sum(mdl.shipment[i, j] for i in mdl.warehouses) == mdl.demand[j]

    def capacity_rule(mdl, i, j):
        return mdl.shipment[i, j] <= mdl.capacity[i, j]

    model.supply_balance = pyo.Constraint(
        model.warehouses, rule=supply_rule
    )
    model.demand_balance = pyo.Constraint(
        model.stores, rule=demand_rule
    )
    model.route_capacity = pyo.Constraint(
        model.warehouses, model.stores, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.shipment[i, j]
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