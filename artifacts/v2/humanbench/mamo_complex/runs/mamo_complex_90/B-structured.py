# IR: {"sets":{"centers":"0..7","stores":"0..7"},"params":{"opening_cost":"params['opening_cost'][i]","transport_cost":"params['transport_cost'][i][j]","demand":"params['demand'][j]","capacity":"params['capacity'][i]"},"variables":{"opened[i]":"Binary","shipment[i,j]":"NonNegativeReals"},"constraints":["For each store j: sum_i shipment[i,j] == demand[j]","For each center i: sum_j shipment[i,j] <= capacity[i]*opened[i]"],"objective":"Minimize sum_i opening_cost[i]*opened[i] + sum_i,j transport_cost[i][j]*shipment[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the facility-location problem using zero-based input arrays."""
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.centers = pyo.RangeSet(0, 7)
    model.stores = pyo.RangeSet(0, 7)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize={i: opening_cost[i] for i in model.centers},
        within=pyo.Reals,
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize={
            (i, j): transport_cost[i][j]
            for i in model.centers
            for j in model.stores
        },
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.stores,
        initialize={j: demand[j] for j in model.stores},
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize={i: capacity[i] for i in model.centers},
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(instance, j):
        return (
            sum(instance.shipment[i, j] for i in instance.centers)
            == instance.demand[j]
        )

    model.demand_balance = pyo.Constraint(
        model.stores, rule=demand_rule
    )

    def capacity_rule(instance, i):
        return (
            sum(instance.shipment[i, j] for j in instance.stores)
            <= instance.capacity[i] * instance.opened[i]
        )

    model.capacity_limit = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[i] * model.opened[i]
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
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}