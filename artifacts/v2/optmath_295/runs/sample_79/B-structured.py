# IR: {"sets":{"I":"0..7","J":"0..5"},"params":{"supplies":"params['supplies'][i]","demands":"params['demands'][j]","transport_cost":"params['transport_cost'][i][j]","route_capacity":"params['route_capacity'][i][j]"},"variables":{"shipment[i,j]":"nonnegative continuous"},"constraints":["sum(j in J, shipment[i,j]) = supplies[i] for i in I","sum(i in I, shipment[i,j]) = demands[j] for j in J","shipment[i,j] <= route_capacity[i,j] for i in I, j in J"],"objective":"minimize sum(i in I, j in J, transport_cost[i,j] * shipment[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supplies = params["supplies"]
    demands = params["demands"]
    transport_cost = params["transport_cost"]
    route_capacity = params["route_capacity"]

    model = pyo.ConcreteModel()
    model.warehouses = pyo.RangeSet(0, 7)
    model.stores = pyo.RangeSet(0, 5)

    model.shipment = pyo.Var(
        model.warehouses,
        model.stores,
        domain=pyo.NonNegativeReals,
    )

    model.supply_balance = pyo.Constraint(
        model.warehouses,
        rule=lambda mdl, i: sum(
            mdl.shipment[i, j] for j in mdl.stores
        ) == supplies[i],
    )

    model.demand_balance = pyo.Constraint(
        model.stores,
        rule=lambda mdl, j: sum(
            mdl.shipment[i, j] for i in mdl.warehouses
        ) == demands[j],
    )

    model.route_limit = pyo.Constraint(
        model.warehouses,
        model.stores,
        rule=lambda mdl, i, j: (
            mdl.shipment[i, j] <= route_capacity[i][j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            transport_cost[i][j] * model.shipment[i, j]
            for i in model.warehouses
            for j in model.stores
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}