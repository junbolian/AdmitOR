# IR: {"sets":{"centers":"1..5","stores":"1..9"},"params":{"opening_cost":"nonnegative vector, params['opening_cost'][i-1]","transport_cost":"nonnegative matrix, params['transport_cost'][i-1][j-1]","demand":"nonnegative vector, params['demand'][j-1]","capacity":"nonnegative vector, params['capacity'][i-1]"},"variables":{"is_open[i]":"binary","shipment[i,j]":"nonnegative continuous"},"constraints":["For each store j: sum_i shipment[i,j] = demand[j]","For each center i: sum_j shipment[i,j] <= capacity[i]*is_open[i]"],"objective":"Minimize sum_i opening_cost[i]*is_open[i] + sum_i,j transport_cost[i,j]*shipment[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-based input vectors and a row-major cost matrix."""
    model = pyo.ConcreteModel()

    model.centers = pyo.RangeSet(1, 5)
    model.stores = pyo.RangeSet(1, 9)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize=lambda _, i: params["opening_cost"][i - 1],
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize=lambda _, i, j: params["transport_cost"][i - 1][j - 1],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.stores,
        initialize=lambda _, j: params["demand"][j - 1],
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize=lambda _, i: params["capacity"][i - 1],
        within=pyo.NonNegativeReals,
    )

    model.is_open = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(block, j):
        return (
            sum(block.shipment[i, j] for i in block.centers)
            == block.demand[j]
        )

    model.demand_fulfillment = pyo.Constraint(
        model.stores, rule=demand_rule
    )

    def capacity_rule(block, i):
        return (
            sum(block.shipment[i, j] for j in block.stores)
            <= block.capacity[i] * block.is_open[i]
        )

    model.center_capacity = pyo.Constraint(
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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}