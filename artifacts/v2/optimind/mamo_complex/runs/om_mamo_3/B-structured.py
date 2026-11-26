# IR: {"sets":{"centers":"0..7","stores":"0..4"},"params":{"opening_cost":"params['opening_cost'][i]","transport_cost":"params['transport_cost'][i][j]","demand":"params['demand'][j]","capacity":"params['capacity'][i]"},"variables":{"is_open[i]":"Binary","shipment[i,j]":"NonNegativeReals"},"constraints":["For each store j: sum_i shipment[i,j] = demand[j]","For each center i: sum_j shipment[i,j] <= capacity[i] * is_open[i]"],"objective":"Minimize sum_i opening_cost[i] * is_open[i] + sum_i,j transport_cost[i,j] * shipment[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-based input sequences; transport_cost is an 8-by-5 matrix."""
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.centers = pyo.RangeSet(0, 7)
    model.stores = pyo.RangeSet(0, 4)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize=lambda mdl, i: opening_cost[i],
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize=lambda mdl, i, j: transport_cost[i][j],
    )
    model.demand = pyo.Param(
        model.stores,
        initialize=lambda mdl, j: demand[j],
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize=lambda mdl, i: capacity[i],
    )

    model.is_open = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, j):
        return (
            sum(mdl.shipment[i, j] for i in mdl.centers)
            == mdl.demand[j]
        )

    model.demand_constraints = pyo.Constraint(
        model.stores, rule=demand_rule
    )

    def capacity_rule(mdl, i):
        return (
            sum(mdl.shipment[i, j] for j in mdl.stores)
            <= mdl.capacity[i] * mdl.is_open[i]
        )

    model.capacity_constraints = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[i] * model.is_open[i]
                for i in model.centers
            )
            + sum(
                model.transport_cost[i, j] * model.shipment[i, j]
                for i in model.centers
                for j in model.stores
            )
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