# IR: {"sets":{"Origins":"0..6","Destinations":"0..6"},"params":{"supply":"nonnegative[Origins]","demand":"nonnegative[Destinations]","cost":"real[Origins,Destinations]","capacity":"nonnegative[Origins,Destinations]"},"variables":{"shipment":"continuous nonnegative[Origins,Destinations]"},"constraints":["For each i: sum_j shipment[i,j] = supply[i]","For each j: sum_i shipment[i,j] = demand[j]","For each i,j: shipment[i,j] <= capacity[i,j]"],"objective":"minimize sum_i sum_j cost[i,j] * shipment[i,j]"}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept vectors indexed by integers and nested or tuple-keyed matrices."""
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    def matrix_entry(data, i, j):
        if isinstance(data, Mapping) and (i, j) in data:
            return data[i, j]
        return data[i][j]

    model = pyo.ConcreteModel()
    model.Origins = pyo.RangeSet(0, 6)
    model.Destinations = pyo.RangeSet(0, 6)

    model.supply = pyo.Param(
        model.Origins,
        initialize=lambda mdl, i: supply[i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.Destinations,
        initialize=lambda mdl, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.Origins,
        model.Destinations,
        initialize=lambda mdl, i, j: matrix_entry(cost, i, j),
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.Origins,
        model.Destinations,
        initialize=lambda mdl, i, j: matrix_entry(capacity, i, j),
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.Origins,
        model.Destinations,
        domain=pyo.NonNegativeReals,
    )

    model.supply_balance = pyo.Constraint(
        model.Origins,
        rule=lambda mdl, i: sum(
            mdl.shipment[i, j] for j in mdl.Destinations
        ) == mdl.supply[i],
    )
    model.demand_balance = pyo.Constraint(
        model.Destinations,
        rule=lambda mdl, j: sum(
            mdl.shipment[i, j] for i in mdl.Origins
        ) == mdl.demand[j],
    )
    model.route_limits = pyo.Constraint(
        model.Origins,
        model.Destinations,
        rule=lambda mdl, i, j: mdl.shipment[i, j] <= mdl.capacity[i, j],
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.shipment[i, j]
            for i in model.Origins
            for j in model.Destinations
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