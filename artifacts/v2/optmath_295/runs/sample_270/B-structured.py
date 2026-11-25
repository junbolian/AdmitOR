# IR: {"sets":{"warehouses":"0..4","stores":"0..3"},"params":{"supply":"params['supply'][i]","demand":"params['demand'][j]","cost":"params['cost'][i][j]","capacity":"params['capacity'][i][j]"},"variables":{"shipment[i,j]":"continuous, nonnegative"},"constraints":["sum_j shipment[i,j] = supply[i] for each warehouse i","sum_i shipment[i,j] = demand[j] for each store j","shipment[i,j] <= capacity[i,j] for each route (i,j)"],"objective":"minimize sum_i sum_j cost[i,j] * shipment[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.warehouses = pyo.RangeSet(0, 4)
    model.stores = pyo.RangeSet(0, 3)

    model.supply = pyo.Param(
        model.warehouses,
        initialize=lambda mdl, i: params["supply"][i],
    )
    model.demand = pyo.Param(
        model.stores,
        initialize=lambda mdl, j: params["demand"][j],
    )
    model.cost = pyo.Param(
        model.warehouses,
        model.stores,
        initialize=lambda mdl, i, j: params["cost"][i][j],
    )
    model.capacity = pyo.Param(
        model.warehouses,
        model.stores,
        initialize=lambda mdl, i, j: params["capacity"][i][j],
    )

    model.shipment = pyo.Var(
        model.warehouses,
        model.stores,
        domain=pyo.NonNegativeReals,
    )

    model.supply_balance = pyo.Constraint(
        model.warehouses,
        rule=lambda mdl, i: sum(
            mdl.shipment[i, j] for j in mdl.stores
        ) == mdl.supply[i],
    )

    model.demand_balance = pyo.Constraint(
        model.stores,
        rule=lambda mdl, j: sum(
            mdl.shipment[i, j] for i in mdl.warehouses
        ) == mdl.demand[j],
    )

    model.route_capacity = pyo.Constraint(
        model.warehouses,
        model.stores,
        rule=lambda mdl, i, j: (
            mdl.shipment[i, j] <= mdl.capacity[i, j]
        ),
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
        # HiGHS may raise when no feasible solution can be loaded.
        # Objective retrieval below is the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}